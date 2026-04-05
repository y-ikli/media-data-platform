"""
Pipeline run logger for execution tracking and audit.

Writes a summary record to BigQuery (mdp_marts.run_summary) after each pipeline run.
Each record captures extraction counts, dbt test results, volume check status,
duration, and any errors — providing a full audit trail of pipeline executions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from google.cloud import bigquery  # pylint: disable=no-name-in-module

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:  # pylint: disable=too-many-instance-attributes
    """Groups all pipeline run metadata into a single object."""

    run_id: str
    dag_id: str
    run_date: str
    execution_date: datetime
    status: str
    google_ads_result: dict = field(default_factory=dict)
    meta_ads_result: dict = field(default_factory=dict)
    dbt_test_result: dict | None = None
    dbt_docs_result: dict | None = None
    volume_check_result: dict | None = None
    error_message: str | None = None
    error_task: str | None = None


def _parse_dbt_results(dbt_test_result: dict | None) -> dict:
    """Extract dbt run/test status and test counts from the task result."""
    if not dbt_test_result:
        return {
            "dbt_run_status": "not_run",
            "dbt_test_status": "not_run",
            "dbt_test_passed": 0,
            "dbt_test_failed": 0,
            "dbt_test_warnings": 0,
        }

    output = dbt_test_result.get("output", "")
    return {
        "dbt_run_status": "success" if dbt_test_result.get("success") else "failed",
        "dbt_test_status": dbt_test_result.get("status", "unknown"),
        "dbt_test_passed": output.count("PASS"),
        "dbt_test_failed": output.count("FAIL"),
        "dbt_test_warnings": output.count("WARN"),
    }


def _parse_volume_results(volume_check_result: dict | None) -> dict:
    """Extract volume check status and table counts from the task result."""
    if not volume_check_result:
        return {
            "volume_check_status": "not_run",
            "volume_check_tables_checked": 0,
            "volume_check_tables_passed": 0,
            "volume_check_tables_warned": 0,
            "volume_check_tables_failed": 0,
        }

    summary = volume_check_result.get("summary", {})
    return {
        "volume_check_status": volume_check_result.get("overall_status", "unknown"),
        "volume_check_tables_checked": summary.get("total_tables", 0),
        "volume_check_tables_passed": summary.get("passed", 0),
        "volume_check_tables_warned": summary.get("warned", 0),
        "volume_check_tables_failed": summary.get("failed", 0),
    }


def log_run_summary(project_id: str, summary: RunSummary) -> dict[str, Any]:
    """
    Insert a pipeline run summary record into BigQuery.

    Args:
        project_id: GCP project ID
        summary: RunSummary dataclass with all run metadata

    Returns:
        Dictionary with log status and run_id

    Raises:
        Exception: If BigQuery insert fails
    """
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.mdp_marts.run_summary"

    end_time = datetime.utcnow()
    duration_seconds = int((end_time - summary.execution_date).total_seconds())

    dbt_fields = _parse_dbt_results(summary.dbt_test_result)
    volume_fields = _parse_volume_results(summary.volume_check_result)

    row = {
        "run_id": summary.run_id,
        "dag_id": summary.dag_id,
        "run_date": summary.run_date,
        "execution_date": summary.execution_date.isoformat(),
        "start_time": summary.execution_date.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds,
        "status": summary.status,
        "google_ads_extracted_count": summary.google_ads_result.get("record_count", 0),
        "google_ads_status": summary.google_ads_result.get("status", "unknown"),
        "meta_ads_extracted_count": summary.meta_ads_result.get("record_count", 0),
        "meta_ads_status": summary.meta_ads_result.get("status", "unknown"),
        "dbt_docs_generated": (
            summary.dbt_docs_result.get("docs_generated", False)
            if summary.dbt_docs_result else False
        ),
        "error_message": summary.error_message,
        "error_task": summary.error_task,
        "created_at": end_time.isoformat(),
        "updated_at": end_time.isoformat(),
        **dbt_fields,
        **volume_fields,
    }

    try:
        errors = client.insert_rows_json(table_id, [row])
        if errors:
            logger.error("Failed to insert run summary: %s", errors)
            return {"status": "failed", "errors": errors}

        logger.info("Successfully logged run summary: %s", summary.run_id)
        return {"status": "success", "run_id": summary.run_id, "table_id": table_id}

    except Exception as e:  # pylint: disable=broad-exception-caught
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
        run_id, dag_id, run_date, execution_date,
        duration_seconds, status,
        google_ads_status, meta_ads_status,
        dbt_test_status, volume_check_status
    FROM `{project_id}.mdp_marts.run_summary`
    ORDER BY execution_date DESC
    LIMIT {limit}
    """

    try:
        results = client.query(query).result()
        return [
            {
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
            }
            for row in results
        ]

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error retrieving recent runs: %s", e)
        raise
