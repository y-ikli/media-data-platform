# Quick Start

## Prérequis

- Python 3.13 + [uv](https://docs.astral.sh/uv/)
- Compte GCP avec BigQuery activé
- Service account GCP avec rôle `BigQuery Admin`

## 1. Installation

```bash
git clone https://github.com/y-ikli/media-data-platform.git
cd media-data-platform

uv venv .venv --python 3.13
source .venv/bin/activate
uv sync --dev

cp .env.example .env
# Remplir .env : GCP_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS
```

## 2. Initialiser BigQuery

```bash
set -a && source .env && set +a
bash scripts/setup_bigquery.sh
```

Crée les 4 datasets : `mdp_raw`, `mdp_staging`, `mdp_intermediate`, `mdp_marts`.

## 3. Ingestion des données

```bash
# Meta Ads — vraie API (nécessite META_ADS_* dans .env)
python scripts/ingest_meta_ads.py --start 2023-04-01 --end 2025-09-15

# Google Ads — simulation (mêmes dates pour comparaison cohérente)
python -c "
import sys; sys.path.insert(0, 'src')
from dotenv import load_dotenv; load_dotenv()
from ingestion.google_ads.connector import run
run('2023-04-23', '2025-08-25')
"
```

## 4. Transformations dbt

```bash
cd dbt/mdp
dbt deps --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
```

Résultat attendu : `PASS=4` (run) et `PASS=36` (test).

## 5. Vérifier les données

```bash
python scripts/test_bigquery.py --project media-data-platform --datasets
```

## Troubleshooting

**`GOOGLE_APPLICATION_CREDENTIALS` non trouvé**
```bash
set -a && source .env && set +a
echo $GOOGLE_APPLICATION_CREDENTIALS
```

**Permission denied BigQuery**
→ Vérifier que le service account a le rôle `BigQuery Admin` dans GCP IAM.

**Token Meta expiré**
→ Générer un nouveau token sur developers.facebook.com → Graph API Explorer.
→ Mettre à jour `META_ADS_ACCESS_TOKEN` dans `.env`.
