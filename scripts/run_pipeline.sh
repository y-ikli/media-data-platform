#!/bin/bash
# Full pipeline: ingest Meta Ads + Google Ads → dbt run + test
# Usage: bash scripts/run_pipeline.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables
set -a
source "$PROJECT_DIR/.env"
set +a

# Activate venv
source "$PROJECT_DIR/.venv/bin/activate"

echo "=============================="
echo "  Media Data Platform Pipeline"
echo "=============================="

# --- Meta Ads ingestion (par année pour éviter timeout API) ---
echo ""
echo "[1/5] Meta Ads — 2023"
python "$SCRIPT_DIR/ingest_meta_ads.py" --start 2023-04-01 --end 2023-12-31

echo ""
echo "[2/5] Meta Ads — 2024"
python "$SCRIPT_DIR/ingest_meta_ads.py" --start 2024-01-01 --end 2024-12-31

echo ""
echo "[3/5] Meta Ads — 2025"
python "$SCRIPT_DIR/ingest_meta_ads.py" --start 2025-01-01 --end 2025-09-15

# --- Google Ads ingestion ---
echo ""
echo "[4/5] Google Ads — 2023-2025 (simulation)"
python -c "
import sys
sys.path.insert(0, '$PROJECT_DIR/src')
from dotenv import load_dotenv
load_dotenv('$PROJECT_DIR/.env')
from ingestion.google_ads.connector import run
result = run('2023-04-23', '2025-08-25')
print(f'Google Ads: {len(result)} lignes écrites')
"

# --- dbt transformations ---
echo ""
echo "[5/5] dbt run + test"
cd "$PROJECT_DIR/dbt/mdp"
dbt run --profiles-dir . --no-partial-parse
dbt test --profiles-dir . --no-partial-parse

echo ""
echo "=============================="
echo "  Pipeline terminé avec succès"
echo "=============================="