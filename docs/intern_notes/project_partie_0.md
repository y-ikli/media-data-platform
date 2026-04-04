# Partie 0 

## Objectif
Cadrer le MVP, fixer les conventions et produire les documents de référence **avant toute implémentation**.

---

## Action 0.1 — Créer les dossiers et fichiers de cadrage

```bash
mkdir -p docs config
touch docs/architecture.md
touch docs/data_model.md
touch config/settings.example.yaml
```

---

## Action 0.2 — Définir le MVP 

À écrire dans `README.md` ou en tête de `docs/architecture.md` :

```text
MVP :
- Sources : google_ads, meta_ads
- Data product principal : mart_marketing__campaign_daily
- Grain : 1 ligne = campaign_id × date × platform
- KPI : impressions, clicks, spend, conversions, CTR, CPA, ROAS
- Orchestration prévue : Airflow
```

---

## Action 0.3 — Rédiger `docs/architecture.md`

À faire (contenu minimum attendu) :

```text
- Description du contexte métier
- Schéma logique : sources → ingestion → raw → dbt → marts → usages
- Rôle de chaque composant (GCS, BigQuery, dbt, Airflow)
- Principes :
  - découplage ingestion / transformation
  - SQL-first
  - ingestion incrémentale et idempotente
```

---

## Action 0.4 — Rédiger `docs/data_model.md`

À remplir explicitement :

```text
1) Datasets BigQuery
   - mdp_raw
   - mdp_staging
   - mdp_marts

2) Conventions de nommage
   - raw_<source>__<entity>
   - stg_<source>__<entity>
   - int_<domain>__<entity>
   - mart_<domain>__<grain>

3) Grain analytique
   - Clé d’unicité : (date, platform, campaign_id)

4) Colonnes standard
   - date
   - platform
   - account_id
   - campaign_id
   - campaign_name
   - impressions
   - clicks
   - spend
   - conversions

5) Formules KPI
   - CTR = clicks / impressions
   - CPA = spend / conversions
   - ROAS = revenue / spend (optionnel)
```

---

## Action 0.5 — Créer la configuration d’exemple

À compléter dans `config/settings.example.yaml` :

```yaml
project:
  project_id: your-gcp-project-id
  region: europe-west1

datasets:
  raw: mdp_raw
  staging: mdp_staging
  marts: mdp_marts

ingestion:
  timezone: UTC
  start_date: "2024-01-01"
```

---

## Action 0.6 — Validation finale 

À vérifier avant de continuer :

```text
- docs/architecture.md existe et décrit clairement l’architecture
- docs/data_model.md fixe zones, naming, grain et KPI
- settings.example.yaml couvre les paramètres essentiels
- Le MVP tient en une dizaine de lignes maximum
```

