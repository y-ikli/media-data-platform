-- Table: run_summary
-- Purpose: Track all pipeline execution runs with metadata, status, and metrics
-- Used for: Monitoring, alerting, dashboard analytics

CREATE TABLE IF NOT EXISTS `data-pipeline-platform-484814.mdp_marts.run_summary` (
  run_id STRING NOT NULL,
  dag_id STRING NOT NULL,
  run_date DATE NOT NULL,
  execution_date TIMESTAMP NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP,
  duration_seconds INT64,
  status STRING NOT NULL,  -- 'running', 'success', 'failed', 'partial'
  
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

-- Create a view for recent runs (last 30 days)
CREATE OR REPLACE VIEW `data-pipeline-platform-484814.mdp_marts.vw_recent_runs` AS
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
FROM `data-pipeline-platform-484814.mdp_marts.run_summary`
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY execution_date DESC;
