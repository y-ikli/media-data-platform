# Media Data Platform

[![CI](https://github.com/y-ikli/media-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/y-ikli/media-data-platform/actions)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![dbt](https://img.shields.io/badge/dbt-1.10%2B-orange)
![BigQuery](https://img.shields.io/badge/BigQuery-europe--west1-red)

Pipeline ELT qui centralise les performances publicitaires (Meta Ads, Google Ads) dans BigQuery et produit des tables analytiques fiables : CTR, CPC, CPA, taux de conversion, ROAS, par plateforme, campagne et période.

## Le problème

Chaque plateforme a son schéma, ses noms de colonnes et ses corrections tardives. Sans socle commun, les mêmes KPI sont recalculés de façons différentes dans chaque tableau de bord, et relancer une extraction duplique les lignes. Ce projet fournit **un grain unique, des KPI définis une fois, des chargements rejouables et des données testées**.

## État des données (à lire avant tout chiffre)

| Source | Mode | Détail |
|---|---|---|
| Meta Ads | API réelle **ou** simulée | Le mode réel (`--mode real`) extrait les insights par campagne et par jour ; il demande des identifiants Meta |
| Google Ads | **Simulée** | Générateur déterministe. L'extraction réelle (GAQL) n'est pas implémentée : la demander échoue explicitement |

Toute ligne porte `data_mode` (`real` ou `simulated`), propagé jusqu'aux tables finales : un tableau de bord public doit filtrer ou afficher cette colonne ([ADR-0003](docs/adr/0003-donnees-simulees-etiquetees.md)). Les commandes ci-dessous fonctionnent sans compte GCP ni Meta.

## Essayer sans cloud (2 minutes)

```bash
git clone https://github.com/y-ikli/media-data-platform.git && cd media-data-platform
make install
make ingest-demo    # extrait et valide les deux sources simulées (dry-run)
make dbt-duckdb     # zone raw locale (DuckDB) → dbt build : modèles, 47 tests de données, 4 tests unitaires
```

## Architecture

```
Meta Ads API ─┐                                        ┌─► mart_campaign_daily (incrémental)
              ├─► validation ─► remplacement de fenêtre ─► raw ─► staging ─► intermediate ─┼─► mart_platform_monthly
Google Ads ───┘   (contrat de     idempotent (BigQuery)          dédup       union         └─► dim_campaign
 (simulé)          données)                                                                        │
                                                                                            Looker Studio
```

Détail, schémas et principes : [docs/architecture.md](docs/architecture.md).

## Ce qui a été fait pour que ce soit fiable

| Sujet | Réalisation | Où |
|---|---|---|
| Chargement rejouable | Table temporaire puis transaction `DELETE` (fenêtre) + `INSERT` ; rejouer donne le même état | [ADR-0001](docs/adr/0001-chargement-idempotent.md), `loader.py` |
| Schéma stable | Schémas BigQuery déclarés, pas d'autodétection ; lot invalide rejeté avant chargement | `schemas.py`, `validation.py` |
| Grain garanti | Déduplication en staging (dernière ingestion gagne) et unicité testée à chaque couche | `stg_*`, tests dbt |
| KPI justes | ROAS = valeur de conversion / dépense (l'ancien « ROAS » était un nombre de conversions par dollar) ; ratios mensuels calculés depuis les sommes ; NULL ≠ 0 | [docs/kpi_reference.md](docs/kpi_reference.md) |
| Incrémental | `insert_overwrite` partitionné par jour, fenêtre glissante de 7 jours pour les corrections tardives, `reprocess_from` et `--full-refresh` | `mart_campaign_daily.sql`, [runbook](docs/runbook.md) |
| Environnements | Cibles `duckdb`, `dev` (`mdp_dev_*`), `prod` (`mdp_*`) ; aucune clé JSON lue par le projet | `profiles.yml`, `generate_schema_name` |
| CI qui peut échouer | Tests dbt réels sur DuckDB, sqlfluff, tests Python (couverture ≥ 85 %), `dbt parse` BigQuery | [ADR-0002](docs/adr/0002-dbt-duckdb-ci.md), `.github/workflows/ci.yml` |

## Structure

```
src/mdp/
  ingestion/   base, schemas, validation, loader (BigQuery), connecteurs, CLI `mdp-ingest`
  fake_apis/   générateur déterministe de données simulées
  dev/         zone raw DuckDB pour dbt sans cloud
dbt/mdp/       models (staging, intermediate, marts), macros, tests unitaires, profiles.yml
tests/         unit (ingestion) et dbt (exécution réelle sur DuckDB)
docs/          architecture, modèle de données, KPI, exploitation, ADR
```

## Utiliser avec BigQuery

```bash
cp .env.example .env                      # renseigner GCP_PROJECT_ID
gcloud auth application-default login
uv run mdp-ingest --source meta_ads --start 2024-01-01 --end 2024-03-31
uv run mdp-ingest --source google_ads --start 2024-01-01 --end 2024-03-31
make dbt-build                            # cible dev : jeux de données mdp_dev_*
```

Exploitation (rejouer une période, lire un échec) : [docs/runbook.md](docs/runbook.md).

## Limites connues

- Le chargement et les modèles sont testés hors BigQuery (client simulé, DuckDB). Le SQL rendu pour BigQuery n'est pas exécuté en CI (`dbt parse` seulement).
- Aucun tableau de bord n'est versionné : les marts sont conçus pour Looker Studio, sans capture dans ce dépôt.
- Pas d'orchestration planifiée : l'ingestion se lance à la main ou depuis un planificateur externe.
- Google Ads simulé ; devises non converties (tout en USD).

## Feuille de route

1. **Cloud-natif** : Terraform (jeux de données, comptes de service à moindre privilège, Secret Manager), ingestion en Cloud Run Job déclenché par Cloud Scheduler, authentification GitHub → GCP par Workload Identity Federation, exécution de dbt sur un projet BigQuery de test en CI.
2. **Observabilité** : fraîcheur et volumétrie alertées (Cloud Monitoring), documentation dbt publiée.
3. **Optionnel, streaming** : événements de conversion (Pub/Sub → Dataflow → BigQuery) pour un vrai revenu par campagne.

## Licence

Apache License 2.0.
