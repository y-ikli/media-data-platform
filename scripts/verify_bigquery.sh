#!/bin/bash
# Quick verification script for BigQuery setup

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          BIGQUERY VERIFICATION SCRIPT                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if credentials are set
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  GOOGLE_APPLICATION_CREDENTIALS not set"
    echo ""
    echo "To verify BigQuery, first set your credentials:"
    echo "  export GOOGLE_APPLICATION_CREDENTIALS=~/path/to/gcp-key.json"
    echo ""
    exit 0
fi

echo "✓ Credentials found: $GOOGLE_APPLICATION_CREDENTIALS"
echo ""

# Step 1: Check connection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1 Testing BigQuery Connection..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYEOF'
from google.cloud import bigquery
import sys

try:
    client = bigquery.Client()
    project_id = client.project
    print(f"✓ Connected to BigQuery!")
    print(f"✓ Project ID: {project_id}")
    print("")
except Exception as e:
    print(f"✗ Connection failed: {str(e)}")
    sys.exit(1)
PYEOF

echo ""

# Step 2: List datasets
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2 Checking Datasets..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bq ls --project_id=data-pipeline-platform-484814

echo ""

# Step 3: List raw tables
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3 Tables in mdp_raw (Ingestion Output)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bq ls data-pipeline-platform-484814:mdp_raw 2>/dev/null || echo "  mdp_raw dataset not yet created (run setup_bigquery.sh)"

echo ""

# Step 4: Check for data
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4  Checking for Ingested Data..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bq query --use_legacy_sql=false '
SELECT 
  TABLE_NAME,
  TIMESTAMP_MILLIS(CREATION_TIME) as created_at,
  ROW_COUNT,
  ROUND(SIZE_BYTES/1024/1024, 2) as size_mb
FROM `data-pipeline-platform-484814.mdp_raw.__TABLES__`
ORDER BY CREATION_TIME DESC
' 2>/dev/null || echo "ℹ️  No tables in mdp_raw yet (trigger ingestion DAGs)"

echo ""

# Step 5: List staging tables
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5 Tables in mdp_staging (After dbt)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bq ls data-pipeline-platform-484814:mdp_staging 2>/dev/null || echo " mdp_staging is empty (run: dbt run)"

echo ""

# Step 6: List marts tables
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6  Tables in mdp_marts (Analytics Layer)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bq ls data-pipeline-platform-484814:mdp_marts 2>/dev/null || echo "ℹ️  mdp_marts is empty (run: dbt run)"

echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    NEXT STEPS                                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Trigger ingestion DAGs in Airflow:"
echo "   - google_ads_ingestion_raw"
echo "   - meta_ads_ingestion_raw"
echo ""
echo "2. Check tables appear in mdp_raw"
echo ""
echo "3. Run dbt transformations:"
echo "   cd dbt/mdp && dbt run"
echo ""
echo "4. Check mart_campaign_daily in mdp_marts"
echo ""
echo "5. View data in Google Cloud Console:"
echo "   https://console.cloud.google.com/bigquery"
echo ""
