# Architecture — Marketing Data Platform

## Contexte métier

Une organisation marketing exploite des données de performance issues de plateformes publicitaires (**Google Ads**, **Meta Ads**, etc).

**Défis principaux :**
- Données distribuées sur plusieurs sources (APIs, formats hétérogènes)
- Définitions de KPI non harmonisées entre plateformes
- Mises à jour non uniformes (retards, corrections tardives)
- Difficultés à industrialiser un reporting fiable et maintenable

**Solution :** Construire un **socle data centralisé** transformant ces flux en **tables analytiques réutilisables**.

---

## Flux end-to-end

```
Google Ads API    Meta Ads API
    ↓                 ↓
  Ingestion Python (extraction quotidienne + late data handling)
    ↓
Raw Zone (mdp_raw — données brutes + métadonnées)
    ↓
dbt Transformations
    ├─ Staging (typage, nettoyage)
    ├─ Intermediate (unification multi-sources)
    └─ Marts (KPI finalisés)
    ↓
BigQuery Analytics (mdp_staging, mdp_marts)
    ↓
Usages (BI, Dashboards, Analyses ad-hoc)
```

---

## Architecture par couche

### 1. Ingestion (Python + Airflow)

**Responsabilités :**
- Extraction quotidienne des données sources
- Idempotence garantie (rejouabilité sans doublons)
- Traçabilité complète (extract_run_id, ingested_at)

**Patterns :**
- Watermark par `date` (fenêtre = today + 7 jours retro pour late data)
- Partitionnement par `date` + `source`
- Chaque run génère un UUID unique (`extract_run_id`)

**Actuellement implémenté :**
- Architecture abstraite (classe `DataSourceConnector`)
- Connecteurs : `GoogleAdsConnector`, `MetaAdsConnector`
- DAGs Airflow : `google_ads_ingestion.py`, `meta_ads_ingestion.py`

---

### 2. Raw Zone (mdp_raw)

**Responsabilités :**
- Historiser les données brutes, telles que reçues
- Permettre rejoueabilité et audit complet

**Conventions :**
- Tables : `raw_<source>__<entity>` (ex: `raw_google_ads__campaign_daily`)
- Partitioning : par `date`
- Colonnes de metadata : `ingested_at`, `extract_run_id`, `source`

**Clé de chargement :** `(date, platform, campaign_id, extract_run_id)`

---

### 3. Staging Zone (mdp_staging — Partie Staging)

**Responsabilités :**
- Typage et validation des colonnes
- Flagging de qualité (anomalies détectées)
- Normalisation des noms de colonnes
- Ajout constant de `platform`

**Conventions :**
- Tables : `stg_<source>__<entity>`
- Colonne supplémentaire : `is_invalid_*` (flags de qualité)

**Exemple :**
```sql
SELECT
  CAST(date AS DATE) AS date,
  'google_ads' AS platform,
  CAST(impressions AS INT64) AS impressions,
  CASE WHEN clicks > impressions THEN TRUE ELSE FALSE END AS is_invalid_clicks
FROM mdp_raw.raw_google_ads__campaign_daily
```

---

### 4. Intermediate Zone (mdp_staging — Partie Unification)

**Responsabilités :**
- Union des sources (Google Ads + Meta Ads)
- Déduplication (garde dernière version par extract_run_id)
- Schéma commun multi-plateforme

**Conventions :**
- Tables : `int_<domain>__<entity>` (ex: `int_campaign__daily_unified`)

---

### 5. Marts Zone (mdp_marts)

**Responsabilités :**
- Tables analytiques prêtes pour BI / Reporting
- KPI calculés et validés
- Grain analytique stabilisé

**Conventions :**
- Tables : `mart_<domain>__<grain>` (ex: `mart_campaign__daily`)
- Partitioning par `date`, clustering par `platform` + `campaign_id`

**Exemple :**
```sql
SELECT
  date,
  platform,
  campaign_id,
  impressions,
  clicks,
  spend,
  conversions,
  SAFE_DIVIDE(clicks, impressions) AS ctr,
  SAFE_DIVIDE(spend, conversions) AS cpa
FROM mdp_staging.int_campaign__daily_unified
```

---

## Grain analytique (clé métier)

**Définition :** 1 ligne = 1 campagne × 1 date × 1 plateforme

**Clé d'unicité :**
```
PRIMARY KEY (date, platform, campaign_id)
```

**Raison :** Chaque plateforme (Google, Meta) expose ses propres campagnes par date. L'union crée un grain commun pour les analyses consolidées.

---

## KPI exposés

| KPI | Formule | Granularité | Seuil cible |
|-----|---------|-------------|-------------|
| **Impressions** | Métrique brute | campaign × date | - |
| **Clicks** | Métrique brute | campaign × date | - |
| **Spend** | Métrique brute | campaign × date | - |
| **Conversions** | Métrique brute | campaign × date | - |
| **CTR** | clicks / impressions | campaign × date | > 2% |
| **CPA** | spend / conversions | campaign × date | < €5 |
| **Conv. Rate** | conversions / clicks | campaign × date | > 5% |

---

## Principes structurants

### 1. Découplage ingestion / transformation
- Ingestion = capture brute + historisation
- Transformation = logique métier (dbt)
- **Bénéfices :** Rejouabilité, maintenabilité, évolutivité

### 2. SQL-first (dbt)
- Logique analytique versionnée en SQL
- Tests automatisés (not null, unique, accepted values)
- Lineage généré (documentation)

### 3. Idempotence
- Relancer un run = même résultat (pas de doublons)
- Partitionnement par `date` + `run_id`
- Clés stables au grain métier

### 4. Historisation complète
- Append-only (aucune suppression de données)
- Permet audit et time-travel queries

### 5. Séparation des responsabilités
- **Raw :** Confiance 100% à la source
- **Staging :** Nettoyage et standardisation
- **Marts :** Usages analytiques spécifiques

---

## Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Orchestration | Apache Airflow | 2.9.3 |
| Conteneurisation | Docker Compose | - |
| Python | Python | 3.10+ |
| Data Warehouse | BigQuery | - |
| Transformations | dbt | (en cours) |
| Ingestion | Python + APIs | - |
| Versioning | Git | - |

---

## Évolutions post-MVP

- Ajout grains additionnels (adset, ad, keyword)
- Data quality avancée (relationships, freshness checks)
- Observabilité renforcée (metrics de run, SLA, alerting)
- Optimisation BigQuery (clustering, materialized views)
- Data contracts formalisés (schema versioning)
