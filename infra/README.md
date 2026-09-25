# Infrastructure GCP (Terraform)

Décrit tout ce qui entoure le code : jeux de données BigQuery, comptes de service à moindre privilège, Secret Manager, Artifact Registry, trois jobs Cloud Run, un workflow d'orchestration, le planificateur, l'authentification GitHub → GCP sans clé, et les alertes.

> **Statut** : le code est validé (`terraform fmt`, `validate`, tflint, trivy) mais **n'a pas été appliqué sur un vrai projet GCP**. Les points à vérifier au premier apply sont listés en bas.

## Architecture

```
Cloud Scheduler ──► Workflows (mdp-daily) ──┬─► Cloud Run Job mdp-ingest-meta   ─┐  en parallèle
   (06:00 Paris)     compte mdp-scheduler   └─► Cloud Run Job mdp-ingest-google ─┤  compte mdp-ingest
                                                                                ▼
                                            puis ──► Cloud Run Job mdp-dbt (dbt build : modèles + tests)
                                                     compte mdp-dbt
Données : mdp_raw ─► mdp_staging ─► mdp_intermediate ─► mdp_marts ─► Looker Studio
Secrets : Secret Manager (mdp-meta-ads-*), lus seulement par mdp-ingest et seulement en mode real
Déploiement : GitHub Actions ─(OIDC, WIF)─► compte mdp-deployer ─► Artifact Registry + mise à jour des jobs
Alertes : Cloud Monitoring (exécution en échec, aucune exécution réussie depuis 26 h) + budget optionnel
```

Choix et alternatives écartées : [ADR-0004](../docs/adr/0004-cloud-run-jobs-workflows.md) (orchestration), [ADR-0005](../docs/adr/0005-workload-identity-federation.md) (authentification).

## Droits (moindre privilège)

| Compte | Droits | Pourquoi |
|---|---|---|
| `mdp-ingest` | `dataEditor` sur `mdp_raw` ; `bigquery.jobUser` ; `secretAccessor` sur les 4 secrets Meta | écrit dans raw, lit ses identifiants, rien d'autre |
| `mdp-dbt` | `dataViewer` sur `mdp_raw` ; `dataEditor` sur staging, intermediate, marts ; `bigquery.jobUser` | lit raw, construit les couches suivantes |
| `mdp-workflow` | `run.invoker` sur les 3 jobs ; `serviceAccountUser` sur `mdp-ingest` et `mdp-dbt` | lance les jobs, rien d'autre |
| `mdp-scheduler` | `workflows.invoker` (projet) | démarre le workflow |
| `mdp-deployer` | `artifactregistry.writer` (dépôt) ; `run.developer` (projet) ; `serviceAccountUser` sur `mdp-ingest`, `mdp-dbt` | pousse l'image et met à jour les jobs ; **ne peut pas** lire les données ni les secrets |

Aucune clé de compte de service n'existe. GitHub n'obtient `mdp-deployer` que pour ce dépôt **et** la branche configurée (`github_allowed_ref`).

## Premier déploiement

Prérequis : un projet GCP dédié par environnement avec facturation, `gcloud` et `terraform ≥ 1.6`.

```bash
gcloud auth application-default login
./infra/bootstrap.sh <project_id>                       # bucket d'état (une fois)

cd infra
cp envs/dev.tfvars.example envs/dev.tfvars              # renseigner project_id
terraform init -backend-config="bucket=<project_id>-tfstate"
terraform plan  -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars
```

Puis, dans GitHub → Settings → Variables du dépôt, ajouter `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_WIF_PROVIDER` et `GCP_DEPLOYER_SA` (valeurs données par `terraform output`). Le workflow **Deploy** construit l'image, la pousse et met à jour les jobs.

Mode réel Meta : ajouter les valeurs hors bande (elles ne doivent jamais passer par Terraform, qui les écrirait dans l'état) :

```bash
printf '%s' "$META_ADS_ACCESS_TOKEN" | gcloud secrets versions add mdp-meta-ads-access-token --data-file=-
# idem : mdp-meta-ads-app-id, mdp-meta-ads-app-secret, mdp-meta-ads-account-id — puis meta_mode = "real"
```

Premier run manuel avant d'activer le planificateur (`schedule_paused = true` par défaut) :

```bash
gcloud workflows run mdp-daily --location europe-west1
```

## Coût

Ordre de grandeur pour ce volume (quelques milliers de lignes par jour) : jobs Cloud Run de quelques secondes par jour, BigQuery dans le quota gratuit mensuel, Secret Manager et Artifact Registry négligeables : **de l'ordre de quelques euros par mois au plus**. Un budget d'alerte est créé si `billing_account` est renseigné. Cloud Composer (Airflow managé, > 300 €/mois) est écarté pour cette raison.

## À vérifier au premier apply

Ces points ne peuvent pas être validés sans projet réel ; ils sont les plus susceptibles de demander un ajustement :
1. **dbt et les jeux de données** : dbt liste puis, si besoin, crée les jeux de données de ses modèles. Le compte `mdp-dbt` n'a pas `datasets.create` (Terraform les crée). Si `dbt build` échoue sur ce droit, accorder `roles/bigquery.user` à `mdp-dbt`.
2. **Alerte d'absence** : `condition_absent` a une durée maximale ; ajuster `duration` si l'API la refuse.
3. **Workflows → Cloud Run** : vérifier que l'appel `jobs.run` attend bien la fin du job (connecteur à opération longue).
4. **Image initiale** : avant le premier déploiement, les jobs utilisent l'image d'exemple de Google et ne font rien d'utile.

## Qualité du code Terraform

```bash
docker run --rm -v "$PWD/infra:/w" -w /w hashicorp/terraform:1.9 fmt -check -recursive
docker run --rm -v "$PWD/infra:/w" -w /w hashicorp/terraform:1.9 validate   # après init -backend=false
```

La CI exécute `fmt`, `validate`, `tflint` et `trivy config` (workflow *Infra*).
