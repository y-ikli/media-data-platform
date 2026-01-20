"""
Run summary logger for tracking pipeline executions.

This module provides functionality to log pipeline run metadata to BigQuery
for monitoring, alerting, and analytics.
"""

from datetime import datetime
from typing import Any
from google.cloud import bigquery
import logging

logger = logging.getLogger(__name__)


def log_run_summary(
    project_id: str,
    run_id: str,
    dag_id: str,
    run_date: str,
    execution_date: datetime,
    status: str,
    google_ads_result: dict,
    meta_ads_result: dict,
    dbt_test_result: dict | None = None,
    dbt_docs_result: dict | None = None,
    volume_check_result: dict | None = None,
    error_message: str | None = None,
    error_task: str | None = None,
) -> dict[str, Any]:
    """
    Log a pipeline run summary to BigQuery.

    Args:
        project_id: GCP project ID
        run_id: Unique run identifier
        dag_id: DAG identifier
        run_date: Run date (YYYY-MM-DD)
        execution_date: Execution timestamp
        status: Overall status ('running', 'success', 'failed', 'partial')
        google_ads_result: Result dict from Google Ads extraction
        meta_ads_result: Result dict from Meta Ads extraction
        dbt_test_result: Result dict from dbt test task
        dbt_docs_result: Result dict from dbt docs task
        volume_check_result: Result dict from volume check task
        error_message: Error message if failed
        error_task: Task that failed

    Returns:
        Dictionary with log status

    Raises:
        Exception: If BigQuery insert fails
    """
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.mdp_marts.run_summary"

    # Calculate duration if possible
    start_time = execution_date
    end_time = datetime.utcnow()
    duration_seconds = int((end_time - start_time).total_seconds())

    # Parse results
    google_ads_status = google_ads_result.get("status", "unknown")
    google_ads_count = google_ads_result.get("record_count", 0)
    
    meta_ads_status = meta_ads_result.get("status", "unknown")
    meta_ads_count = meta_ads_result.get("record_count", 0)

    # Parse dbt test results
    dbt_run_status = "not_run"
    dbt_test_status = "not_run"
    dbt_test_passed = 0
    dbt_test_failed = 0
    dbt_test_warnings = 0
    
    if dbt_test_result:
        dbt_run_status = "success" if dbt_test_result.get("success") else "failed"
        dbt_test_status = dbt_test_result.get("status", "unknown")
        
        # Parse test counts from output if available
        output = dbt_test_result.get("output", "")
        if "PASS" in output:
            dbt_test_passed = output.count("PASS")
        if "FAIL" in output:
            dbt_test_failed = output.count("FAIL")
        if "WARN" in output:
            dbt_test_warnings = output.count("WARN")

    # Parse dbt docs results
    dbt_docs_generated = False
    if dbt_docs_result:
        dbt_docs_generated = dbt_docs_result.get("docs_generated", False)

    # Parse volume check results
    volume_check_status = "not_run"
    volume_check_tables_checked = 0
    volume_check_tables_passed = 0
    volume_check_tables_warned = 0
    volume_check_tables_failed = 0
    
    if volume_check_result:
        volume_check_status = volume_check_result.get("overall_status", "unknown")
        summary = volume_check_result.get("summary", {})
        volume_check_tables_checked = summary.get("total_tables", 0)
        volume_check_tables_passed = summary.get("passed", 0)
        volume_check_tables_warned = summary.get("warned", 0)
        volume_check_tables_failed = summary.get("failed", 0)

    # Prepare row to insert
    row = {
        "run_id": run_id,
        "dag_id": dag_id,
        "run_date": run_date,
        "execution_date": execution_date.isoformat(),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds,
        "status": status,
        "google_ads_extracted_count": google_ads_count,
        "google_ads_status": google_ads_status,
        "meta_ads_extracted_count": meta_ads_count,
        "meta_ads_status": meta_ads_status,
        "dbt_run_status": dbt_run_status,
        "dbt_test_status": dbt_test_status,
        "dbt_test_passed": dbt_test_passed,
        "dbt_test_failed": dbt_test_failed,
        "dbt_test_warnings": dbt_test_warnings,
        "dbt_docs_generated": dbt_docs_generated,
        "volume_check_status": volume_check_status,
        "volume_check_tables_checked": volume_check_tables_checked,
        "volume_check_tables_passed": volume_check_tables_passed,
        "volume_check_tables_warned": volume_check_tables_warned,
        "volume_check_tables_failed": volume_check_tables_failed,
        "error_message": error_message,
        "error_task": error_task,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    try:
        # Insert row into BigQuery
        errors = client.insert_rows_json(table_id, [row])
        
        if errors:
            logger.error("Failed to insert run summary: %s", errors)
            return {
                "status": "failed",
                "errors": errors,
            }
        
        logger.info("Successfully logged run summary: %s", run_id)
        return {
            "status": "success",
            "run_id": run_id,
            "table_id": table_id,
        }
        
    except Exception as e:
        logger.error("Error logging run summary: %s", e)
        raise


def get_recent_runs(project_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Retrieve recent pipeline runs from BigQuery.

    Args:
        project_id: GCP project ID
        limit: Maximum number of runs to retrieve

    Returns:
        List of run summary dictionaries
    """
    client = bigquery.Client(project=project_id)
    
    query = f"""
    SELECT
        run_id,
        dag_id,
        run_date,
        execution_date,
        duration_seconds,
        status,
        google_ads_status,
        meta_ads_status,
        dbt_test_status,
        volume_check_status
    FROM `{project_id}.mdp_marts.run_summary`
    ORDER BY execution_date DESC
    LIMIT {limit}
    """
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        runs = []
        for row in results:
            runs.append({
                "run_id": row.run_id,
                "dag_id": row.dag_id,
                "run_date": row.run_date.isoformat(),
                "execution_date": row.execution_date.isoformat(),
                "duration_seconds": row.duration_seconds,
                "status": row.status,
                "google_ads_status": row.google_ads_status,
                "meta_ads_status": row.meta_ads_status,
                "dbt_test_status": row.dbt_test_status,
                "volume_check_status": row.volume_check_status,
            })
        
        return runs
        
    except Exception as e:
        logger.error("Error retrieving recent runs: %s", e)
        raise
