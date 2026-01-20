#!/bin/bash
# Script to create the run_summary table and view in BigQuery

set -e

PROJECT_ID="${GCP_PROJECT_ID:-data-pipeline-platform-484814}"
DATASET="mdp_marts"
TABLE="run_summary"
VIEW="vw_recent_runs"

echo "=========================================="
echo "Creating run_summary table in BigQuery"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Dataset: $DATASET"
echo "Table: $TABLE"
echo ""

# Create the table
echo "Creating table $DATASET.$TABLE..."
bq query --use_legacy_sql=false --project_id="$PROJECT_ID" <<EOF
CREATE TABLE IF NOT EXISTS \`$PROJECT_ID.$DATASET.$TABLE\` (
  run_id STRING NOT NULL,
  dag_id STRING NOT NULL,
  run_date DATE NOT NULL,
  execution_date TIMESTAMP NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP,
  duration_seconds INT64,
  status STRING NOT NULL,
  
  -- Extraction metrics
  google_ads_extracted_count INT64,
  google_ads_status STRING,
  meta_ads_extracted_count INT64,
  meta_ads_status STRING,
  
  -- dbt metrics
  dbt_run_status STRING,
  dbt_test_status STRING,
  dbt_test_passed INT64,
  dbt_test_failed INT64,
  dbt_test_warnings INT64,
  dbt_docs_generated BOOL,
  
  -- Volume check metrics
  volume_check_status STRING,
  volume_check_tables_checked INT64,
  volume_check_tables_passed INT64,
  volume_check_tables_warned INT64,
  volume_check_tables_failed INT64,
  
  -- Error tracking
  error_message STRING,
  error_task STRING,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY run_date
CLUSTER BY dag_id, status;
EOF

echo "✓ Table created successfully"
echo ""

# Create the view
echo "Creating view $DATASET.$VIEW..."
bq query --use_legacy_sql=false --project_id="$PROJECT_ID" <<EOF
CREATE OR REPLACE VIEW \`$PROJECT_ID.$DATASET.$VIEW\` AS
SELECT
  run_id,
  dag_id,
  run_date,
  execution_date,
  start_time,
  end_time,
  duration_seconds,
  status,
  google_ads_status,
  meta_ads_status,
  dbt_run_status,
  dbt_test_status,
  volume_check_status,
  CASE
    WHEN status = 'success' THEN '✓'
    WHEN status = 'failed' THEN '✗'
    WHEN status = 'partial' THEN '⚠'
    ELSE '●'
  END AS status_icon
FROM \`$PROJECT_ID.$DATASET.$TABLE\`
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY execution_date DESC;
EOF

echo "✓ View created successfully"
echo ""

echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "You can now query the table:"
echo "  bq query --use_legacy_sql=false 'SELECT * FROM \`$PROJECT_ID.$DATASET.$VIEW\` LIMIT 10'"
echo ""
