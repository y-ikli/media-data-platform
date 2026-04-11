#!/bin/bash
# Test script to validate BigQuery integration

set -e

echo "================================"
echo "Testing BigQuery Integration"
echo "================================"
echo ""

# Test 1: Check dependencies
echo "Test 1: Checking dependencies..."
python3 << 'EOF'
try:
    import google.cloud.bigquery
    print("✓ google-cloud-bigquery installed")
except ImportError:
    print("✗ google-cloud-bigquery not found. Run: pip install -r requirements.txt")
    exit(1)

try:
    from ingestion.base import DataSourceConnector
    print("✓ DataSourceConnector imported")
except ImportError:
    print("✗ Cannot import DataSourceConnector")
    exit(1)

try:
    from fake_apis.google_ads_api import get_campaign_daily
    print("✓ Fake APIs available")
except ImportError:
    print("✗ Cannot import fake APIs")
    exit(1)
EOF
echo ""

# Test 2: Test fake APIs
echo "Test 2: Testing fake APIs..."
python3 << 'EOF'
from fake_apis.google_ads_api import get_campaign_daily as get_google
from fake_apis.meta_ads_api import get_campaign_daily as get_meta

google_data = get_google("2024-01-01", "2024-01-02")
print(f"✓ Google Ads API generated {len(google_data)} records")

meta_data = get_meta("2024-01-01", "2024-01-02")
print(f"✓ Meta Ads API generated {len(meta_data)} records")

# Check fields
print(f"✓ Google Ads record sample: {google_data[0]}")
EOF
echo ""

# Test 3: Test connector logic (without BigQuery)
echo "Test 3: Testing connector logic..."
python3 << 'EOF'
from ingestion.google_ads.connector import GoogleAdsConnector
from ingestion.meta_ads.connector import MetaAdsConnector

# Test Google Ads connector
gac = GoogleAdsConnector()
print(f"✓ GoogleAdsConnector initialized (source: {gac.source_name})")

# Test Meta Ads connector
mac = MetaAdsConnector()
print(f"✓ MetaAdsConnector initialized (source: {mac.source_name})")

# Test extract method
google_raw = gac.extract("2024-01-01", "2024-01-02")
print(f"✓ Extract works: {len(google_raw)} rows")

# Test load_raw enrichment
enriched = gac.load_raw(google_raw[:1])
print(f"✓ Metadata enrichment works")
print(f"  Enriched fields: {list(enriched[0].keys())}")
EOF
echo ""

# Test 4: BigQuery connection (if credentials set)
echo "Test 4: Testing BigQuery connection..."
python3 << 'EOF'
import os
import sys
from google.cloud import bigquery

creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not creds_path:
    print("⚠ GOOGLE_APPLICATION_CREDENTIALS not set")
    print("  Skipping BigQuery connection test")
    print("  To enable: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
    sys.exit(0)

try:
    client = bigquery.Client()
    project_id = client.project
    print(f"✓ Connected to BigQuery (Project: {project_id})")
    
    # Try to list datasets
    try:
        datasets = list(client.list_datasets(max_results=5))
        print(f"✓ Found {len(datasets)} datasets")
    except Exception as e:
        print(f"⚠ Cannot list datasets: {str(e)}")
        
except Exception as e:
    print(f"✗ BigQuery connection failed: {str(e)}")
    print("  Make sure:")
    print("    1. GOOGLE_APPLICATION_CREDENTIALS points to a valid JSON key")
    print("    2. Service account has BigQuery permissions")
    sys.exit(1)
EOF
echo ""

echo "================================"
echo "✓ All tests passed!"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Setup BigQuery: bash scripts/setup_bigquery.sh"
echo "  2. Run full test: pytest tests/unit/test_fake_apis.py -v"
echo "  3. Trigger DAG in Airflow and check BigQuery for data"
