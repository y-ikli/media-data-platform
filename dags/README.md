# Répertoire des DAGs

## Vue d'ensemble

Ce répertoire contient les DAGs Apache Airflow (Graphes Acycliques Dirigés) qui orchestrent les pipelines de la plateforme de données marketing.

## DAGs

### 1. `hello_airflow.py` — Test de santé
**Objectif :** Valide qu'Airflow fonctionne correctement.  
**Schedule :** Quotidien (`@daily`)  
**Status :** ✅ DAG de test (non-production)

### 2. `google_ads_ingestion.py` — Extraction Google Ads
**Objectif :** Extrait les données de campagnes Google Ads depuis l'API vers la couche raw BigQuery.  
**Schedule :** Déclenchement manuel uniquement  
**Source :** Google Ads API  
**Cible :** `mdp_raw.raw_google_ads__campaign_daily`  
**Idempotence :** Full refresh avec déduplication via `extract_run_id`  
**Paramètres :** `start_date`, `end_date` (format ISO)

### 3. `meta_ads_ingestion.py` — Extraction Meta Ads
**Objectif :** Extrait les données de campagnes Meta Ads (Facebook/Instagram) depuis l'API vers la couche raw BigQuery.  
**Schedule :** Déclenchement manuel uniquement  
**Source :** Meta Ads API  
**Cible :** `mdp_raw.raw_meta_ads__campaign_daily`  
**Idempotence :** Full refresh avec déduplication via `extract_run_id`  
**Paramètres :** `start_date`, `end_date` (format ISO)

### 4. `marketing_data_platform.py` — **Orchestrateur Principal** 
**Objectif :** Pipeline end-to-end : extraire toutes les sources → exécuter transformations dbt → tester qualité données.  
**Schedule :** Quotidien à 2 AM UTC  
**Dépendances :** Tous les autres composants (extractions, dbt, BigQuery)  
**Règle de déclenchement :** Manuel ou planifié  
**Durée attendue :** ~5-10 minutes

**Flux de tâches :**
```
Extraction Google Ads ──┐
                         ├──> dbt run ──> dbt test ──> docs ──> summary
Extraction Meta Ads ────┘
```

**Paramètres :** Configuration de run optionnelle avec plage de dates :
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-02"
}
```

Pour une documentation détaillée, voir [marketing_data_platform.md](../docs/dags/marketing_data_platform.md).

---

## Démarrage rapide

### Voir les DAGs dans l'interface Airflow
1. Démarrer Airflow : `docker compose up -d`
2. Ouvrir l'UI : http://localhost:8080
3. Tous les DAGs sont listés sur la page d'accueil

### Déclencher un DAG manuellement

**Via CLI :**
```bash
# Déclencher avec paramètres par défaut
airflow dags test marketing_data_platform 2024-01-20

# Déclencher avec plage de dates personnalisée
airflow dags trigger marketing_data_platform \
  --conf '{"start_date": "2024-02-01", "end_date": "2024-02-05"}'
```

**Via l'interface web :**
1. Cliquer sur le nom du DAG (ex. `marketing_data_platform`)
2. Cliquer sur le bouton **Trigger DAG** (icône ▶)
3. (Optionnel) Ajouter une configuration JSON dans le champ "Configuration"
4. Cliquer sur **Trigger**

### Monitorer un run
1. Trouver le DAG dans l'interface
2. Cliquer sur un run (dans le tableau "Runs")
3. Voir les logs individuels des tâches dans la vue **Graph** ou **Tree**
4. Cliquer sur tâche → **Log** pour déboguer les erreurs

---

## Structure des dossiers

```
dags/
├── hello_airflow.py                    # Test de santé
├── google_ads_ingestion.py             # Extraction Google Ads → raw
├── meta_ads_ingestion.py               # Extraction Meta Ads → raw
└── marketing_data_platform.py          # Orchestrateur principal 
```

---

## Développement

### Ajouter un nouveau DAG

1. Créer un nouveau fichier Python dans ce répertoire (ex. `mon_nouveau_dag.py`)
2. Définir un DAG en utilisant le décorateur `@dag` ou la classe `DAG`
3. Airflow le découvre et le charge automatiquement
4. Pas de redémarrage requis (Airflow a le rechargement à chaud)

### Tester un DAG localement

```bash
# Valider la syntaxe Python
python -m py_compile dags/marketing_data_platform.py

# Tester une tâche unique
airflow tasks test marketing_data_platform dbt_run 2024-01-20
```

### Problèmes courants

| Problème | Solution |
|----------|----------|
| "DAG file not found" | S'assurer que le fichier est dans le répertoire `dags/` et finit par `.py` |
| Tâche échoue avec erreur d'import | Ajouter à `PYTHONPATH` ou ajuster sys.path (voir DAGs ingestion) |
| Credentials manquantes | S'assurer que la variable d'env `GOOGLE_APPLICATION_CREDENTIALS` ou le compte service GCP est configuré |
| Modèles dbt non trouvés | Vérifier le chemin du projet dbt et l'emplacement de `profiles.yml` |

---

## Dépannage

### Un DAG n'apparaît pas dans l'interface
- Vérifier les logs : `docker compose logs airflow-webserver`
- Valider la syntaxe du fichier : `python -m py_compile dags/<dag_name>.py`
- Redémarrer le scheduler : `docker compose restart airflow-scheduler`

### Tâche échoue avec timeout
- Augmenter `execution_timeout` dans la définition de la tâche
- Vérifier les problèmes de réseau/API
- Consulter les logs : Airflow UI → DAG Run → Task → Log

### dbt run échoue
- Vérifier les credentials BigQuery et les permissions des datasets
- Vérifier le profil dbt (`dbt/mdp/profiles.yml`)
- Exécuter localement : `cd dbt/mdp && dbt run`

---

## Variables d'environnement

S'assurer que ces variables sont définies avant d'exécuter les DAGs :

| Variable | Exemple | Objectif |
|----------|---------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | `/path/to/key.json` | Authentification BigQuery |
| `AIRFLOW_HOME` | `/home/airflow` | Répertoire de base Airflow |
| `DBT_PROFILES_DIR` | `dbt/mdp/` | Emplacement configuration dbt |

---
