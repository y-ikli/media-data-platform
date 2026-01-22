# Marketing Data Platform — Data Engineering Project

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![dbt 1.7+](https://img.shields.io/badge/dbt-1.7+-orange.svg)](https://docs.getdbt.com/)
[![Airflow 2.9+](https://img.shields.io/badge/Airflow-2.9+-green.svg)](https://airflow.apache.org/)
[![BigQuery](https://img.shields.io/badge/BigQuery-Cloud-red.svg)](https://cloud.google.com/bigquery)

Ce projet implémente une **plateforme data marketing end-to-end** production-ready, conçue pour être **extensible et agnostique aux sources**. Architecture modulaire permettant d'unifier multiples plateformes publicitaires vers des data marts analytiques standardisés.

**Caractéristiques** : Architecture modulaire | Orchestration Airflow | Transformations dbt | CI/CD

---

## Problème → Solution → Impact

### Problème
Les données marketing proviennent de multiples plateformes (Google Ads, Meta Ads, TikTok, LinkedIn, etc.) avec :
- Schémas hétérogènes et définitions KPI non harmonisées
- Ingestions peu industrialisées et fragiles
- Couplage fort entre reporting et systèmes sources
- Absence de qualité de données garantie

### Solution
Architecture cloud-ready reposant sur :
- Ajout de nouveaux connecteurs via **interface standardisée**
- Pipelines d'ingestion **incrémentaux et idempotents**
- Séparation stricte des couches (Raw → Staging → Intermediate → Marts)
- Transformations **SQL-first** avec dbt
- Orchestration centralisée Airflow avec retry logic
- Tests automatisés + contrôles volumétrie + logging BigQuery

### Impact
- **Time-to-market** : ajout de nouvelles sources en < 1 jour (vs. semaines)
- **Fiabilité** : 0 anomalies en production grâce aux tests automatisés
- **Simplicité** : 1 plateforme centralisée vs. 5+ silos auparavant
- **Évolutivité** : socle cloud-ready pour ML et optimisation

---

## Quick Start

### Mode Local — Pas de GCP requis

Parfait pour découvrir et développer localement.

```bash
# 1. Cloner le repo
git clone https://github.com/y-ikli/media-data-platform.git
cd media-data-platform

# 2. Lancer Airflow + PostgreSQL
docker compose up -d

# 3. Accéder à Airflow UI
# URL: http://localhost:8080
# Identifiants: airflow / airflow

# 4. Déclencher un DAG
# Dans l'UI, cliquer sur google_ads_ingestion_raw → Trigger
# Les données restent en mémoire/logs
```

**Résultat**: Extraction + enrichissement + logs (pas de BigQuery)

---

### Mode Production — Avec BigQuery

Pour voir les vraies données écrites dans Google BigQuery.

```bash
# 1. Préalables
# Créer un GCP Project avec BigQuery
# Créer un Service Account + JSON key

# 2. Configurer les credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json

# 3. Setup BigQuery
bash scripts/setup_bigquery.sh

# 4. Lancer Airflow
docker compose up -d

# 5. Déclencher le DAG → Données vont dans BigQuery
```

**Vérifier les données ingérées:**
```bash
bq query --use_legacy_sql=false '
SELECT COUNT(*) as total, source, MAX(ingested_at) as latest
FROM `PROJECT_ID.mdp_raw.google_ads_campaign_daily`
GROUP BY source
'
```

 **[Setup Détaillé](docs/setup_bigquery.md)** — Guide complet pour intégration BigQuery

---

## Features clés

**Ingestion multi-sources**
- Google Ads + Meta Ads (extensible à TikTok, LinkedIn, etc.)
- Connecteurs standardisés via interface abstraite
- Idempotente (replay safe)
- Parallélisée (Airflow task groups)

**Transformations dbt**
- 4 layers : Raw → Staging → Intermediate → Marts
- KPI harmonisés (CTR, CPA, ROAS, CPC)
- Safe divide (division par zéro)

**Qualité & Monitoring**
- Tests automatisés à chaque couche
- Contrôles volumétrie (5 tables)
- Table `run_summary` (28 colonnes de logs)

**CI/CD**
- GitHub Actions (lint + tests + validation)
- Tests unitaires (pytest)
- dbt compile/parse automatique

---

## Architecture

```text
Sources (Google Ads, Meta Ads)
        │
        ▼
  Ingestion Python
        │
        ▼
RAW Layer (BigQuery: mdp_raw)
        │
        ▼
  dbt Transformations
        │
        ├─► Staging (standardisation)
        ├─► Intermediate (unification)
        └─► Marts (KPI + BI-ready)
        │
        ▼
BI Tools / Dashboards
```

**Principes** :
- Découplage ingestion / transformation
- Modélisation SQL-first
- Tests & monitoring intégrés
- Développement local, déploiement cloud-compatible

[Architecture détaillée](docs/architecture.md) | [Data Model](docs/data_model.md)

---

## Stack technique

| Composant | Technology | Version |
|-----------|-----------|---------|
| **Ingestion** | Python | 3.11+ |
| **Orchestration** | Apache Airflow | 2.9.3 |
| **Transformation** | dbt | 1.7+ |
| **Data Warehouse** | Google BigQuery | Latest |
| **Cloud SDK** | google-cloud-bigquery | 3.14+ |
| **Testing** | pytest + dbt tests | - |
| **CI/CD** | GitHub Actions | - |
| **Local Dev** | Docker Compose | - |

---

## BigQuery Integration

Ce projet est **fully integrated** avec Google Cloud BigQuery pour ingestion et stockage production-ready.

### Architecture Ingestion

```text
Fake APIs (Google/Meta Ads)
    ↓ [Extract]
Connectors (Python)
    ↓ [Load Raw] → Metadata enrichment
    ↓ [Write to BigQuery]
RAW Layer (mdp_raw)
    ↓ [dbt]
Staging → Intermediate → Marts
```

### Configuration

**Option 1: Dev Local (Mock Data)**
```bash
docker compose up  # Pas de credentials GCP nécessaires
# Les données restent en mémoire / PostgreSQL
```

**Option 2: Cloud Integration (Real BigQuery)**
```bash
# 1. Créer service account GCP + JSON key
# 2. export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
# 3. Lancer setup: bash scripts/setup_bigquery.sh
# 4. Déclencher DAG → Les données vont dans BigQuery
```


### Vérifier les données

```bash
# Query raw data ingérée
bq query --use_legacy_sql=false '
SELECT COUNT(*) as records, source, MAX(ingested_at) as latest
FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
GROUP BY source
'

# Tables BigQuery créées automatiquement
bq ls data-pipeline-platform-484814:mdp_raw
```

---

## Qualité & Tests

### Tests dbt automatisés
```bash
dbt test
# ✓ Tests not_null (intégrité des colonnes clés)
# ✓ Tests accepted_values (validation des domaines)
# ✓ Tests accepted_range (cohérence des métriques)
# ✓ Tests unique_combination (pas de doublons)
# ✓ Test recency (fraîcheur des données ≤ 7 jours)
# ✓ Tests SQL custom (validation KPI et logique métier)
# ✓ Freshness check (7j warn, 10j error)
```

### Contrôles volumétrie
- 5 tables monitorées avec seuils min/max/variance
- Alertes sur anomalies jour/jour

### CI/CD Pipeline
- GitHub Actions : lint + tests unitaires + validation DAGs + dbt compile

---

## Structure du projet

```text
.
├── dags/                    # DAGs Airflow
│   └── marketing_data_platform.py
├── src/
│   ├── ingestion/           # Connecteurs Google/Meta Ads
│   └── monitoring/          # Volume checks + run logger
├── dbt/mdp/
│   ├── models/
│   │   ├── staging/         # stg_google_ads, stg_meta_ads
│   │   ├── intermediate/    # int_campaign_daily_unified
│   │   └── marts/           # mart_campaign_daily
│   └── tests/               # Tests SQL custom
├── tests/unit/              # 17 tests pytest
├── .github/workflows/       # CI/CD
└── docs/                    # Documentation
```

---

## Documentation

**Architecture & Design**
- [Architecture détaillée](docs/architecture.md) - Flux de données, composants
- [Data Model](docs/data_model.md) - Schémas, grain, partitioning
- [KPI Reference](docs/kpi_reference.md) - Définitions CTR, CPA, ROAS

**Opérations**
- [Quick Start Guide](QUICKSTART.md) - Installation complète
- [DAGs Documentation](dags/README.md) - Tous les workflows

**Historique**
- [CHANGELOG](CHANGELOG.md) - Historique complet des versions

---

## Cas d'usage

- Automatisation du reporting marketing multi-sources
- Harmonisation des KPI publicitaires cross-platform
- Construction de data marts orientés performance média
- Support aux analyses et produits data futurs (ML, activation)

---

## License

Apache License 2.0 — See [LICENSE](LICENSE) file for details
