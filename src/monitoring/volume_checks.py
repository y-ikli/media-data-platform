"""
Volume control checks for data quality monitoring.

This module provides functions to validate data volumes across the marketing data platform
and detect anomalies (day-over-day variance, min/max thresholds, etc.).
"""

from typing import Any
from google.cloud import bigquery
import logging

logger = logging.getLogger(__name__)


# Define volume thresholds for each table
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


def get_volume_checks(project_id: str) -> dict[str, Any]:
    """
    Execute volume checks for all tables in VOLUME_THRESHOLDS.

    Args:
        project_id: GCP project ID for BigQuery

    Returns:
        Dictionary with check results for each table

    Raises:
        Exception: If BigQuery query fails
    """
    client = bigquery.Client(project=project_id)
    results = {"tables_checked": [], "warnings": [], "errors": [], "summary": {}}

    for table_id, thresholds in VOLUME_THRESHOLDS.items():
        logger.info(f"Checking volume for {table_id}...")

        try:
            # Get today's record count
            today_query = f"""
            SELECT COUNT(*) as record_count
            FROM `{table_id}`
            WHERE DATE(ingested_at) = CURRENT_DATE()
            """

            today_result = client.query(today_query).result()
            today_count = list(today_result)[0]["record_count"]

            # Get yesterday's record count for variance calculation
            yesterday_query = f"""
            SELECT COUNT(*) as record_count
            FROM `{table_id}`
            WHERE DATE(ingested_at) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
            """

            yesterday_result = client.query(yesterday_query).result()
            yesterday_count = (
                list(yesterday_result)[0]["record_count"]
                if list(yesterday_result)
                else 0
            )

            # Calculate variance
            variance_percent = 0
            if yesterday_count > 0:
                variance_percent = abs(today_count - yesterday_count) / yesterday_count * 100

            # Check against thresholds
            table_result = {
                "table": table_id,
                "today_count": today_count,
                "yesterday_count": yesterday_count,
                "variance_percent": round(variance_percent, 2),
                "status": "PASS",
                "issues": [],
            }

            # Min threshold check
            if today_count < thresholds["min_daily_records"]:
                table_result["status"] = "FAIL"
                table_result["issues"].append(
                    f"Record count ({today_count}) below minimum threshold "
                    f"({thresholds['min_daily_records']})"
                )
                results["errors"].append(
                    f"{table_id}: Below minimum threshold "
                    f"({today_count}/{thresholds['min_daily_records']})"
                )

            # Max threshold check
            if today_count > thresholds["max_daily_records"]:
                table_result["status"] = "FAIL"
                table_result["issues"].append(
                    f"Record count ({today_count}) exceeds maximum threshold "
                    f"({thresholds['max_daily_records']})"
                )
                results["errors"].append(
                    f"{table_id}: Exceeds maximum threshold "
                    f"({today_count}/{thresholds['max_daily_records']})"
                )

            # Variance check
            if variance_percent > thresholds["max_variance_percent"]:
                table_result["status"] = "WARN"
                table_result["issues"].append(
                    f"Day-over-day variance ({variance_percent:.1f}%) exceeds threshold "
                    f"({thresholds['max_variance_percent']}%)"
                )
                results["warnings"].append(
                    f"{table_id}: High variance detected "
                    f"({variance_percent:.1f}%, yesterday: {yesterday_count})"
                )

            results["tables_checked"].append(table_result)

            logger.info(
                f"  ✓ {table_id}: {today_count} records (variance: {variance_percent:.1f}%)"
            )

        except Exception as e:
            logger.error(f"  ✗ Error checking {table_id}: {str(e)}")
            results["errors"].append(f"{table_id}: {str(e)}")
            results["tables_checked"].append(
                {
                    "table": table_id,
                    "status": "ERROR",
                    "error": str(e),
                }
            )

    # Summary
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

    logger.info(
        f"Volume check summary: {passed} passed, {warned} warned, {failed} failed, {errored} errored"
    )

    return results


def format_volume_report(results: dict[str, Any]) -> str:
    """
    Format volume check results into a readable report.

    Args:
        results: Dictionary returned by get_volume_checks()

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 80)
    report.append("VOLUME CONTROL CHECK REPORT")
    report.append("=" * 80)
    report.append("")

    # Summary section
    summary = results["summary"]
    report.append(f"Overall Status: {summary['overall_status']}")
    report.append(
        f"Results: {summary['passed']} PASS, {summary['warned']} WARN, "
        f"{summary['failed']} FAIL, {summary['errored']} ERROR"
    )
    report.append("")

    # Details section
    report.append("Table Details:")
    report.append("-" * 80)

    for table in results["tables_checked"]:
        status_icon = {
            "PASS": "✓",
            "WARN": "⚠",
            "FAIL": "✗",
            "ERROR": "❌",
        }.get(table.get("status", "UNKNOWN"), "?")

        report.append(f"{status_icon} {table['table']}")

        if "today_count" in table:
            report.append(
                f"  Today: {table['today_count']} records | "
                f"Yesterday: {table['yesterday_count']} records | "
                f"Variance: {table['variance_percent']}%"
            )

        if table.get("issues"):
            for issue in table["issues"]:
                report.append(f"  ⚠ {issue}")

        if table.get("error"):
            report.append(f"  ✗ Error: {table['error']}")

    report.append("")

    # Warnings and errors sections
    if results["warnings"]:
        report.append("WARNINGS:")
        report.append("-" * 80)
        for warning in results["warnings"]:
            report.append(f"  • {warning}")
        report.append("")

    if results["errors"]:
        report.append("ERRORS:")
        report.append("-" * 80)
        for error in results["errors"]:
            report.append(f"  • {error}")
        report.append("")

    report.append("=" * 80)

    return "\n".join(report)
