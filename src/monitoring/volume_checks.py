"""
Volume control checks for data quality monitoring.

Validates data volumes across all layers of the pipeline (raw, staging, marts)
and detects anomalies: tables below minimum thresholds, above maximum thresholds,
or with abnormal day-over-day variance. Called by the main Airflow DAG after dbt runs.
"""

import logging
from typing import Any
from google.cloud import bigquery  # pylint: disable=no-name-in-module

logger = logging.getLogger(__name__)


VOLUME_THRESHOLDS = {
    "mdp_marts.mart_campaign_daily": {
        "min_daily_records": 10,
        "max_daily_records": 100000,
        "max_variance_percent": 50,
        "description": "Daily campaign performance metrics",
    },
    "mdp_staging.stg_google_ads__campaign_daily": {
        "min_daily_records": 5,
        "max_daily_records": 50000,
        "max_variance_percent": 50,
        "description": "Google Ads staging layer",
    },
    "mdp_staging.stg_meta_ads__campaign_daily": {
        "min_daily_records": 5,
        "max_daily_records": 50000,
        "max_variance_percent": 50,
        "description": "Meta Ads staging layer",
    },
    "mdp_raw.google_ads_campaign_daily": {
        "min_daily_records": 1,
        "max_daily_records": 50000,
        "max_variance_percent": 70,
        "description": "Google Ads raw extraction",
    },
    "mdp_raw.meta_ads_campaign_daily": {
        "min_daily_records": 1,
        "max_daily_records": 50000,
        "max_variance_percent": 70,
        "description": "Meta Ads raw extraction",
    },
}


def _check_thresholds(table_id: str, today_count: int, yesterday_count: int,
                      thresholds: dict, results: dict) -> dict:
    """
    Evaluate a single table against its volume thresholds.

    Args:
        table_id: Fully qualified table name
        today_count: Number of records ingested today
        yesterday_count: Number of records ingested yesterday
        thresholds: Threshold configuration for this table
        results: Shared results dict to append warnings/errors to

    Returns:
        Table result dict with status and issues
    """
    variance_percent = 0.0
    if yesterday_count > 0:
        variance_percent = abs(today_count - yesterday_count) / yesterday_count * 100

    table_result = {
        "table": table_id,
        "today_count": today_count,
        "yesterday_count": yesterday_count,
        "variance_percent": round(variance_percent, 2),
        "status": "PASS",
        "issues": [],
    }

    min_rec = thresholds["min_daily_records"]
    max_rec = thresholds["max_daily_records"]
    max_var = thresholds["max_variance_percent"]

    if today_count < min_rec:
        table_result["status"] = "FAIL"
        table_result["issues"].append(
            f"Record count ({today_count}) below minimum threshold ({min_rec})"
        )
        results["errors"].append(
            f"{table_id}: Below minimum threshold ({today_count}/{min_rec})"
        )

    if today_count > max_rec:
        table_result["status"] = "FAIL"
        table_result["issues"].append(
            f"Record count ({today_count}) exceeds maximum threshold ({max_rec})"
        )
        results["errors"].append(
            f"{table_id}: Exceeds maximum threshold ({today_count}/{max_rec})"
        )

    if variance_percent > max_var:
        table_result["status"] = "WARN"
        table_result["issues"].append(
            f"Day-over-day variance ({variance_percent:.1f}%) exceeds threshold ({max_var}%)"
        )
        results["warnings"].append(
            f"{table_id}: High variance ({variance_percent:.1f}%, yesterday: {yesterday_count})"
        )

    return table_result


def _query_count(client: bigquery.Client, table_id: str, date_filter: str) -> int:
    """
    Query record count for a table filtered by ingested_at date.

    Args:
        client: BigQuery client
        table_id: Fully qualified table name
        date_filter: SQL date expression (e.g. 'CURRENT_DATE()')

    Returns:
        Record count as integer
    """
    query = (
        f"SELECT COUNT(*) as record_count FROM `{table_id}` "
        f"WHERE DATE(ingested_at) = {date_filter}"
    )
    rows = list(client.query(query).result())
    return rows[0]["record_count"] if rows else 0


def get_volume_checks(project_id: str) -> dict[str, Any]:
    """
    Execute volume checks for all tables in VOLUME_THRESHOLDS.

    Args:
        project_id: GCP project ID for BigQuery

    Returns:
        Dictionary with check results for each table
    """
    client = bigquery.Client(project=project_id)
    results = {"tables_checked": [], "warnings": [], "errors": [], "summary": {}}

    for table_id, thresholds in VOLUME_THRESHOLDS.items():
        logger.info("Checking volume for %s...", table_id)

        try:
            today_count = _query_count(client, table_id, "CURRENT_DATE()")
            yesterday_count = _query_count(
                client, table_id, "DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)"
            )

            table_result = _check_thresholds(
                table_id, today_count, yesterday_count, thresholds, results
            )
            results["tables_checked"].append(table_result)
            logger.info("  %s: %d records (variance: %.1f%%)",
                        table_id, today_count, table_result["variance_percent"])

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Any BigQuery error (table not found, permission denied, etc.) is caught here
            logger.error("  Error checking %s: %s", table_id, str(e))
            results["errors"].append(f"{table_id}: {str(e)}")
            results["tables_checked"].append(
                {"table": table_id, "status": "ERROR", "error": str(e)}
            )

    passed = sum(1 for t in results["tables_checked"] if t["status"] == "PASS")
    warned = sum(1 for t in results["tables_checked"] if t["status"] == "WARN")
    failed = sum(1 for t in results["tables_checked"] if t["status"] == "FAIL")
    errored = sum(1 for t in results["tables_checked"] if t["status"] == "ERROR")

    results["summary"] = {
        "total_tables": len(results["tables_checked"]),
        "passed": passed,
        "warned": warned,
        "failed": failed,
        "errored": errored,
        "overall_status": "PASS" if failed == 0 and errored == 0 else "FAIL",
    }

    logger.info("Volume check summary: %d passed, %d warned, %d failed, %d errored",
                passed, warned, failed, errored)

    return results


def format_volume_report(results: dict[str, Any]) -> str:
    """
    Format volume check results into a readable report string.

    Args:
        results: Dictionary returned by get_volume_checks()

    Returns:
        Formatted report string
    """
    summary = results["summary"]
    report = [
        "=" * 80,
        "VOLUME CONTROL CHECK REPORT",
        "=" * 80,
        "",
        f"Overall Status: {summary['overall_status']}",
        f"Results: {summary['passed']} PASS, {summary['warned']} WARN, "
        f"{summary['failed']} FAIL, {summary['errored']} ERROR",
        "",
        "Table Details:",
        "-" * 80,
    ]

    for table in results["tables_checked"]:
        status_icon = {"PASS": "v", "WARN": "!", "FAIL": "x", "ERROR": "E"}.get(
            table.get("status", "UNKNOWN"), "?"
        )
        report.append(f"{status_icon} {table['table']}")

        if "today_count" in table:
            report.append(
                f"  Today: {table['today_count']} | "
                f"Yesterday: {table['yesterday_count']} | "
                f"Variance: {table['variance_percent']}%"
            )

        for issue in table.get("issues", []):
            report.append(f"  ! {issue}")

        if table.get("error"):
            report.append(f"  x Error: {table['error']}")

    if results["warnings"]:
        report += ["", "WARNINGS:", "-" * 80]
        report += [f"  * {w}" for w in results["warnings"]]

    if results["errors"]:
        report += ["", "ERRORS:", "-" * 80]
        report += [f"  * {e}" for e in results["errors"]]

    report.append("=" * 80)
    return "\n".join(report)
