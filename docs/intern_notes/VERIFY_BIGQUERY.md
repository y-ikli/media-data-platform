# Vérifier BigQuery - Guide Rapide

## Résumé du Flux

```
Ingestion DAGs (Airflow)
    ↓
Fake APIs générèrent données
    ↓
Données écrites → mdp_raw (BigQuery)
    ↓
dbt transformations
    ↓
mdp_staging, mdp_intermediate, mdp_marts
```

---

## Comment Vérifier

### 1. **Setup Initial**

```bash
# Définir credentials
export GOOGLE_APPLICATION_CREDENTIALS=~/gcp-key.json

# Initialiser datasets
bash scripts/setup_bigquery.sh
```

### 2. **Vérifier la Connexion**

```bash
# Lancer le script de vérification
bash scripts/verify_bigquery.sh
```

**Ou manuellement:**

```bash
# Liste tous les datasets
bq ls --project_id=data-pipeline-platform-484814

# Devrait afficher:
# datasetId
# ----------
# mdp_raw
# mdp_staging
# mdp_intermediate
# mdp_marts
```

### 3. **Après Trigger DAG (Ingestion)**

```bash
# Voir les tables créées
bq ls data-pipeline-platform-484814:mdp_raw

# Devrait afficher:
# tableId                      Type    Labels  Time partitioning
# -------------------------    ------  ------  ------------------
# google_ads_campaign_daily    TABLE
# meta_ads_campaign_daily      TABLE
```

### 4. **Vérifier les Données Ingérées**

```bash
# Combien de lignes?
bq query --use_legacy_sql=false '
SELECT 
  COUNT(*) as total_rows,
  source,
  MIN(ingested_at) as premiere_ingest,
  MAX(ingested_at) as derniere_ingest
FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
GROUP BY source
'

# Résultat attendu:
# total_rows | source      | premiere_ingest | derniere_ingest
# -----------|-------------|-----------------|----------------
# 125        | google_ads  | 2024-12-01...   | 2024-12-31...
```

### 5. **Voir les Données (Preview)**

```bash
# Affiche les 10 premières lignes
bq query --use_legacy_sql=false '
SELECT * 
FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
LIMIT 10
'
```

### 6. **Après dbt run (Transformations)**

```bash
# Vérifier staging tables
bq ls data-pipeline-platform-484814:mdp_staging

# Devrait afficher:
# stg_google_ads__campaign_daily
# stg_meta_ads__campaign_daily
```

### 7. **Vérifier Marts (Analytique)**

```bash
# Voir les données agrégées
bq query --use_legacy_sql=false '
SELECT 
  date,
  source,
  COUNT(*) as num_campaigns,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks,
  SUM(conversions) as total_conversions,
  ROUND(SUM(cost_usd), 2) as total_spend
FROM `data-pipeline-platform-484814.mdp_marts.mart_campaign_daily`
GROUP BY date, source
ORDER BY date DESC
LIMIT 10
'
```

---

## Alternativa: Google Cloud Console (GUI)

**Easiest way to explore visually:**

1. Ouvrir: https://console.cloud.google.com/bigquery
2. Select project: `data-pipeline-platform-484814`
3. In left panel → Expand your project
4. See datasets: `mdp_raw`, `mdp_staging`, `mdp_intermediate`, `mdp_marts`
5. Click table → **Preview** tab (voir les données)
6. Click table → **Schema** tab (voir les colonnes)
7. Write custom queries in editor

---

## Commandes Utiles

### Schema d'une table

```bash
bq show data-pipeline-platform-484814:mdp_raw.google_ads_campaign_daily
```

### Statistiques de table

```bash
bq show --format=pretty data-pipeline-platform-484814:mdp_raw.google_ads_campaign_daily
```

### Query avec alias de projet

```bash
bq query '
SELECT COUNT(*) as total 
FROM data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily
'
```

### Exporter résultat en JSON/CSV

```bash
# Export to JSON
bq query --use_legacy_sql=false \
  --format=json \
  'SELECT * FROM data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily LIMIT 100' \
  > output.json

# Export to CSV
bq query --use_legacy_sql=false \
  --format=csv \
  'SELECT * FROM data-pipeline-platform-484314.mdp_marts.mart_campaign_daily' \
  > output.csv
```

---

## Checklist - Est-ce que c'est OK?

### ✅ Connection

- [ ] `bq ls` fonctionne
- [ ] 4 datasets existent

### ✅ Ingestion (après DAG trigger)

- [ ] `mdp_raw.google_ads_campaign_daily` a des données
- [ ] `mdp_raw.meta_ads_campaign_daily` a des données
- [ ] `ingested_at` timestamp est récent
- [ ] `source` column = "google_ads" ou "meta_ads"

### ✅ Transformations (après `dbt run`)

- [ ] `mdp_staging.stg_google_ads__campaign_daily` existe
- [ ] `mdp_staging.stg_meta_ads__campaign_daily` existe
- [ ] `mdp_intermediate.int_campaign_daily_unified` existe
- [ ] `mdp_marts.mart_campaign_daily` existe

### ✅ Data Quality (après `dbt test`)

- [ ] Tous les tests passent
- [ ] Volume checks OK (pas d'anomalies)

---

## Troubleshooting

### Error: "Dataset not found"

```bash
# Créer les datasets
bash scripts/setup_bigquery.sh
```

### Error: "Permission denied"

```bash
# Vérifier que le service account a les bons rôles
# Dans IAM Console: https://console.cloud.google.com/iam-admin/iam
# Le service account doit avoir:
#   - BigQuery Admin
#   - BigQuery Data Editor
```

### Error: "GOOGLE_APPLICATION_CREDENTIALS not found"

```bash
# Vérifier le chemin
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Si non défini:
export GOOGLE_APPLICATION_CREDENTIALS=~/gcp-key.json
```

### No data in tables

```bash
# 1. Vérifier que les DAGs ont été triggés
# 2. Checker les logs Airflow
# 3. Vérifier que le service account a accès à BigQuery
```

---

## Ressources

- [bq CLI docs](https://cloud.google.com/bigquery/docs/bq-command-line-tool)
- [BigQuery Console](https://console.cloud.google.com/bigquery)
- [Project BIGQUERY_SETUP.md](../docs/BIGQUERY_SETUP.md)
