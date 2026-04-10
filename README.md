# Marketing Data Platform

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![dbt 1.11+](https://img.shields.io/badge/dbt-1.11+-orange.svg)](https://docs.getdbt.com/)
[![BigQuery](https://img.shields.io/badge/BigQuery-Cloud-red.svg)](https://cloud.google.com/bigquery)
[![CI](https://github.com/y-ikli/media-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/y-ikli/media-data-platform/actions)

Pipeline ELT de données marketing centralisant les performances publicitaires multi-sources (Meta Ads, Google Ads) vers des data marts analytiques dans Google BigQuery.

---

## Contexte

Une campagne publicitaire est terminée. On veut analyser ses performances : CTR, CPC, CPA, ROAS — par plateforme, par campagne, par période.

Chaque plateforme expose ses propres schémas et nommages. Ce projet construit le socle de données qui normalise tout en une table analytique unique, cohérente et validée.

---

## État des données

| Source | Mode | Détail |
|--------|------|--------|
| **Meta Ads** | API réelle | Campagnes historiques 2023-04-23 → 2025-08-25 (447 lignes, 46 campagnes, $1 402 spend) |
| **Google Ads** | Simulation | Données générées sur la même période — connecteur prêt pour une vraie API |

---

## Architecture

```
Meta Ads API (réelle)          Google Ads (simulé)
        │                              │
        ▼                              ▼
  Python connector             Python connector
  (facebook-business SDK)      (fake API — même interface)
        │                              │
        └──────────────┬───────────────┘
                       ▼
              mdp_raw (BigQuery)
              Données brutes + métadonnées d'ingestion
              (partitionné par date, idempotent)
                       │
                       ▼
              dbt Transformations
              ├─► Staging       — typage, nettoyage, standardisation par source
              ├─► Intermediate  — union des schémas multi-sources
              └─► Marts         — KPI calculés, prêts pour la BI
                       │
                       ▼
              Looker Studio dashboard
```

> **En production** avec des campagnes actives, un orchestrateur comme Apache Airflow
> déclencherait ce pipeline quotidiennement pour ingérer les nouvelles données J-1,
> relancer dbt et valider la qualité automatiquement.

---

## Compétences illustrées

### Ingestion Python — pattern Strategy

Tous les connecteurs héritent d'une classe abstraite `DataSourceConnector` :

```
DataSourceConnector (abstract)
├── extract()            ← implémenté par chaque source
├── load_raw()           ← enrichissement metadata (ingested_at, extract_run_id)
└── write_to_bigquery()  ← écriture en WRITE_APPEND, déduplication par partition possible
```

Chaque run génère un `extract_run_id` (UUID) pour tracer quelle exécution a produit quelle ligne.
Ajouter une nouvelle source (TikTok, LinkedIn...) ne nécessite d'implémenter que `extract()`.

### Modélisation BigQuery — architecture Medallion

| Dataset | Rôle | Matérialisation |
|---------|------|-----------------|
| `mdp_raw` | Données brutes, audit complet | Table partitionnée par date |
| `mdp_staging` | Standardisation par source | Vue dbt |
| `mdp_intermediate` | Union des sources, schéma commun | Vue dbt |
| `mdp_marts` | KPI finaux, optimisés pour la lecture | Table clusterisée |

### Transformations dbt — KPI calculés une seule fois

| KPI | Formule | Protection |
|-----|---------|------------|
| CTR | `clicks / impressions` | `SAFE_DIVIDE` → null si impressions = 0 |
| CPC | `spend / clicks` | `SAFE_DIVIDE` → null si clicks = 0 |
| CPA | `spend / conversions` | `SAFE_DIVIDE` → null si conversions nulles (Meta) |
| ROAS | `conversions / spend` | `SAFE_DIVIDE` → null si spend = 0 |
| Taux conversion | `conversions / clicks` | `SAFE_DIVIDE` → null si clicks = 0 |

Grain : **1 ligne = 1 campagne × 1 date × 1 plateforme**

### Qualité des données — 36 tests dbt

- `not_null` sur toutes les clés et métriques
- `accepted_values` sur `platform` (google_ads | meta_ads)
- `unique_combination_of_columns` sur (report_date, campaign_id, platform)
- Tests SQL personnalisés : CTR ≤ 100%, clicks ≤ impressions, métriques ≥ 0, formules KPI

### CI/CD — GitHub Actions

- Lint Python (`pylint`)
- Tests unitaires (`pytest`)
- Compilation et parsing dbt (sans credentials BigQuery)

---

## Structure du projet

```
.
├── src/
│   ├── ingestion/           # Connecteurs Meta Ads et Google Ads
│   │   ├── base.py          # Classe abstraite + write BigQuery
│   │   ├── meta_ads/        # Connecteur API réelle (facebook-business)
│   │   └── google_ads/      # Connecteur fake API (même interface)
│   ├── fake_apis/           # Générateurs de données simulées
│   └── monitoring/          # Contrôles volumétrie + logging d'exécution
├── dbt/mdp/
│   └── models/
│       ├── staging/         # stg_meta_ads__campaign_daily, stg_google_ads__campaign_daily
│       ├── intermediate/    # int_campaign_daily_unified (UNION ALL)
│       └── marts/           # mart_campaign_daily (table finale + KPI)
├── scripts/
│   ├── ingest_meta_ads.py   # Ingestion Meta Ads standalone
│   ├── setup_bigquery.sh    # Initialisation datasets BigQuery
│   └── deduplicate_raw.py   # Déduplication tables raw
├── tests/unit/              # Tests pytest (structure dbt, fake APIs)
├── .github/workflows/       # CI GitHub Actions
└── docs/                    # Architecture, modèle de données, référence KPI
```

---

## Lancer le projet

### Prérequis

- Python 3.13 + [uv](https://docs.astral.sh/uv/)
- Compte GCP avec BigQuery + service account JSON
- (Optionnel) Compte Meta Ads avec accès API

### Installation

```bash
git clone https://github.com/y-ikli/media-data-platform.git
cd media-data-platform

# Créer l'environnement local
uv venv .venv --python 3.13
source .venv/bin/activate
uv sync --dev

# Configurer les credentials
cp .env.example .env
# Remplir .env avec vos valeurs
```

### Ingestion

```bash
source .venv/bin/activate
set -a && source .env && set +a

# Meta Ads (vraie API)
python scripts/ingest_meta_ads.py --start 2023-04-01 --end 2025-09-15

# Google Ads (simulation)
python -c "
import sys; sys.path.insert(0, 'src')
from dotenv import load_dotenv; load_dotenv()
from ingestion.google_ads.connector import run
run('2023-04-23', '2025-08-25')
"
```

### Transformations dbt

```bash
cd dbt/mdp
dbt run --profiles-dir .
dbt test --profiles-dir .
```

---

## Documentation

| Document | Contenu |
|----------|---------|
| [Architecture](docs/architecture.md) | Flux de données, composants, principes de conception |
| [Modèle de données](docs/data_model.md) | Schémas, grain, partitionnement, clustering |
| [Référence KPI](docs/kpi_reference.md) | Définitions et formules CTR, CPA, ROAS, CPC |

---

## Licence

Apache License 2.0
