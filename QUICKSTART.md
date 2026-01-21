# Quick Start Guide

Ce guide couvre les deux façons d'utiliser le projet.

## Table of Contents

- [Option 1: Local Mode (Quick Demo)](#option-1-local-mode-quick-demo)
- [Option 2: Production Mode (BigQuery)](#option-2-production-mode-bigquery)
- [Troubleshooting](#troubleshooting)

---

## Option 1: Local Mode (Quick Demo)

**Temps**: 5 minutes  
**Prérequis**: Docker, Docker Compose  
**Résultat**: Voir les DAGs en action, données en logs

### Step 1: Clone et Setup

```bash
git clone https://github.com/y-ikli/media-data-platform.git
cd media-data-platform
```

### Step 2: Lancer les Services

```bash
docker compose up -d
```

Cela démarre:
- Airflow Webserver (http://localhost:8080)
- Airflow Scheduler
- PostgreSQL (metadata)

### Step 3: Accéder à Airflow UI

Ouvrir [http://localhost:8080](http://localhost:8080)

**Identifiants par défaut:**
- Username: `airflow`
- Password: `airflow`

### Step 4: Déclencher un DAG

1. Aller à **DAGs**
2. Trouver `google_ads_ingestion_raw`
3. Cliquer sur le DAG
4. Cliquer **Trigger** (en haut à droite)
5. Entrer une configuration (optionnel):
   ```json
   {
     "start_date": "2024-12-01",
     "end_date": "2024-12-31"
   }
   ```

### Step 5: Voir les Résultats

Attendre que le DAG complète (1-2 min):
- ✓ Task `ingest_google_ads_raw` réussit
- Cliquer sur le task pour voir les logs
- Les données sont extraites et enrichies

### Step 6: Arrêter les Services

```bash
docker compose down
```

---

## Option 2: Production Mode (BigQuery)

**Temps**: 15 minutes  
**Prérequis**: GCP Project avec BigQuery  
**Résultat**: Vraies données écrites dans BigQuery

### Phase 1: Setup GCP Service Account

#### 1a. Créer Service Account

Aller à [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)

1. Cliquer **Create Service Account**
2. Remplir:
   - Service account name: `mdp-airflow`
   - Description: `Airflow connector for Marketing Data Platform`
3. Cliquer **Create and Continue**

#### 1b. Attribuer Permissions

1. Dans "Grant this service account access to project":
2. Ajouter les rôles:
   - ✓ `BigQuery Admin`
   - ✓ `BigQuery Data Editor`
   - ✓ `Storage Object Admin` (optionnel)
3. Cliquer **Continue** → **Done**

#### 1c. Créer une JSON Key

1. Dans la liste des Service Accounts, cliquer sur `mdp-airflow`
2. Aller à l'onglet **Keys**
3. Cliquer **Add Key** → **Create new key**
4. Choisir **JSON**
5. Un fichier JSON se télécharge automatiquement

**Important**: Sauvegarder ce fichier quelque part sûr (ex: `~/mdp-gcp-key.json`)

### Phase 2: Configurer le Projet Local

#### 2a. Définir la Variable d'Environnement

**Bash (Linux/Mac):**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/mdp-gcp-key.json
```

**Windows (PowerShell):**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\mdp-gcp-key.json"
```

**Vérifier:**
```bash
echo $GOOGLE_APPLICATION_CREDENTIALS
# Doit afficher le chemin
```

#### 2b. (Optionnel) Ajouter à docker-compose.yaml

Si vous voulez que les containers Airflow aient accès aux credentials:

```yaml
airflow-webserver:
  environment:
    GOOGLE_APPLICATION_CREDENTIALS: /opt/airflow/gcp-key.json
  volumes:
    - ~/mdp-gcp-key.json:/opt/airflow/gcp-key.json:ro

airflow-scheduler:
  environment:
    GOOGLE_APPLICATION_CREDENTIALS: /opt/airflow/gcp-key.json
  volumes:
    - ~/mdp-gcp-key.json:/opt/airflow/gcp-key.json:ro
```

### Phase 3: Initialiser BigQuery

```bash
bash scripts/setup_bigquery.sh
```

**Output attendu:**
```
✓ Successfully connected to BigQuery
✓ Project ID: data-pipeline-platform-484814
✓ Dataset 'mdp_raw' exists
✓ Dataset 'mdp_staging' exists
✓ Dataset 'mdp_intermediate' exists
✓ Dataset 'mdp_marts' exists
✓ BigQuery setup complete!
```

Si vous voyez des erreurs:
- ➜ Vérifier que `GOOGLE_APPLICATION_CREDENTIALS` est défini
- ➜ Vérifier que le service account a les bonnes permissions

### Phase 4: Lancer Airflow avec BigQuery

```bash
docker compose up -d
```

### Phase 5: Déclencher l'Ingestion

1. Ouvrir [http://localhost:8080](http://localhost:8080)
2. Trigger `google_ads_ingestion_raw`
3. Attendre que le task complète
4. **Chercher dans les logs:**
   ```
   ✓ Successfully loaded 125 rows to mdp_raw.google_ads_campaign_daily
   ```

### Phase 6: Vérifier les Données dans BigQuery

**Option A: Avec bq CLI**

```bash
# Lister les tables
bq ls data-pipeline-platform-484814:mdp_raw

# Query les données
bq query --use_legacy_sql=false '
SELECT COUNT(*) as record_count, source
FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
GROUP BY source
'
```

**Option B: Console Google Cloud**

1. Aller à [BigQuery Console](https://console.cloud.google.com/bigquery)
2. Sélectionner votre project
3. Naviguer: `mdp_raw` → `google_ads_campaign_daily`
4. Cliquer **Preview** pour voir les données

### Phase 7: Vérifier les Transformations dbt

Une fois les données dans `mdp_raw`, les transformations dbt s'exécutent:

```bash
# Naviguer dans BigQuery et vérifier:
# - mdp_staging.stg_google_ads__campaign_daily
# - mdp_intermediate.int_campaign_daily_unified
# - mdp_marts.mart_campaign_daily
```

---

## Troubleshooting

### Q: "docker compose up" échoue

**Vérifier:**
```bash
docker --version
docker-compose --version
```

**Solution:**
```bash
# Mettre à jour Docker Desktop
# Ou installer docker-compose:
pip install docker-compose
```

---

### Q: Airflow UI ne répond pas

**Vérifier les logs:**
```bash
docker compose logs airflow-webserver
```

**Relancer:**
```bash
docker compose restart airflow-webserver
```

---

### Q: "GOOGLE_APPLICATION_CREDENTIALS not found"

**Vérifier:**
```bash
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS
```

**Solution:**
```bash
# Définir le chemin correct:
export GOOGLE_APPLICATION_CREDENTIALS=/home/user/mdp-gcp-key.json

# Vérifier:
echo $GOOGLE_APPLICATION_CREDENTIALS
```

---

### Q: "Permission denied" en BigQuery

**Cause:** Service account n'a pas les bonnes permissions

**Solution:**
1. Aller à [IAM Console](https://console.cloud.google.com/iam-admin/iam)
2. Trouver `mdp-airflow@project-id.iam.gserviceaccount.com`
3. Cliquer le crayon pour éditer
4. Ajouter roles:
   - BigQuery Admin
   - BigQuery Data Editor

---

### Q: DAG déclenché mais aucune donnée dans BigQuery

**Vérifier les logs:**
1. Dans Airflow UI, cliquer sur le DAG run
2. Cliquer sur le task `ingest_google_ads_raw`
3. Vérifier les logs pour des erreurs

**Vérifier l'extraction:**
```bash
# Logs doivent contenir:
# "Extracted 25 records from fake API"
# "Enriched 25 rows with metadata"
# "Successfully loaded 25 rows to mdp_raw.google_ads_campaign_daily"
```

---

### Q: "Table already exists" error

**C'est normal!** Cela signifie:
- Les données sont appendées (pas remplacées)
- Chaque trigger ajoute de nouvelles lignes
- C'est le comportement attendu

---

## Next Steps

1. **Exécuter les transformations dbt**
   ```bash
   cd dbt/mdp
   dbt run
   dbt test
   ```

2. **Examiner les schémas dbt**
   - [Architecture](docs/architecture.md)
   - [Data Model](docs/data_model.md)

3. **Configurer les APIs réelles**
   - Remplacer `fake_apis` par vraies Google Ads API
   - Ajouter Meta Ads API
   - (Voir `docs/BIGQUERY_SETUP.md` pour les détails)

---

## Resources

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [Google BigQuery Docs](https://cloud.google.com/bigquery/docs)
- [dbt Documentation](https://docs.getdbt.com/)
- [Project Architecture](docs/architecture.md)

