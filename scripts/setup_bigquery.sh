#!/bin/bash
# Setup script for BigQuery integration

set -e

echo "================================"
echo "BigQuery Setup for MDP"
echo "================================"
echo ""

# Check if GOOGLE_APPLICATION_CREDENTIALS is already set
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✓ GOOGLE_APPLICATION_CREDENTIALS already set: $GOOGLE_APPLICATION_CREDENTIALS"
    echo ""
else
    echo "GOOGLE_APPLICATION_CREDENTIALS is not set."
    echo ""
    echo "To enable BigQuery integration, you need to:"
    echo ""
    echo "1. Create a GCP Service Account:"
    echo "   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts"
    echo "   - Create service account with name: 'mdp-airflow'"
    echo "   - Grant roles: 'BigQuery Admin', 'BigQuery Data Editor'"
    echo ""
    echo "2. Create and download a JSON key:"
    echo "   - In Service Account details, go to 'Keys' tab"
    echo "   - Click 'Add Key' → 'Create new key' → 'JSON'"
    echo "   - Save the file (e.g., ~/gcp-key.json)"
    echo ""
    echo "3. Set the environment variable:"
    echo "   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json"
    echo ""
    echo "4. Or add to docker-compose.yaml:"
    echo "   environment:"
    echo "     GOOGLE_APPLICATION_CREDENTIALS: /opt/airflow/gcp-key.json"
    echo "   volumes:"
    echo "     - ~/gcp-key.json:/opt/airflow/gcp-key.json:ro"
    echo ""
fi

echo "Testing BigQuery connection..."
echo ""

python3 << 'EOF'
import sys
import os
from google.cloud import bigquery

try:
    # Get credentials path
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print("⚠ GOOGLE_APPLICATION_CREDENTIALS not set")
        print("  BigQuery integration is not yet configured")
        sys.exit(0)
    
    # Test BigQuery connection
    client = bigquery.Client()
    project_id = client.project
    
    print(f"✓ Successfully connected to BigQuery")
    print(f"✓ Project ID: {project_id}")
    print("")
    
    # Check if datasets exist, create if not
    datasets = ["mdp_raw", "mdp_staging", "mdp_intermediate", "mdp_marts"]
    for dataset_id in datasets:
        full_dataset_id = f"{project_id}.{dataset_id}"
        try:
            client.get_dataset(full_dataset_id)
            print(f"✓ Dataset '{dataset_id}' exists")
        except Exception:
            print(f"  Creating dataset '{dataset_id}'...")
            dataset = bigquery.Dataset(full_dataset_id)
            dataset.location = "europe-west1"
            created = client.create_dataset(dataset)
            print(f"✓ Created dataset '{dataset_id}'")
    
    print("")
    print("================================")
    print("✓ BigQuery setup complete!")
    print("================================")
    
except ImportError:
    print("⚠ Google Cloud libraries not installed")
    print("  Run: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {str(e)}")
    print("")
    print("Make sure:")
    print("  1. GOOGLE_APPLICATION_CREDENTIALS is set correctly")
    print("  2. The service account has BigQuery permissions")
    print("  3. The GCP project ID is correct")
    sys.exit(1)
EOF
