"""
End-to-end Marketing Data Platform orchestration DAG.

This DAG orchestrates the complete data pipeline:
1. Extract Google Ads raw data
2. Extract Meta Ads raw data
3. Run dbt transformations (staging → intermediate → marts)
4. Run dbt tests to validate data quality

Schedule: Daily at 2 AM UTC (after typical data availability)
Manual triggers accept optional: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
"""

# pylint: disable=unused-import, import-error

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import pendulum  # type: ignore[import]
from airflow.decorators import dag, task # type: ignore[import]
from airflow.utils.trigger_rule import TriggerRule  # type: ignore[import]

# Add 'src' folder to PYTHONPATH to enable local module imports
_SRC_DIR = (Path(__file__).resolve().parents[1] / "src").as_posix()
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Import ingestion connectors
try:
    from ingestion.google_ads.connector import run as run_google_ads  # type: ignore[import]
    from ingestion.meta_ads.connector import run as run_meta_ads  # type: ignore[import]
except ImportError as e:
    logging.error("Failed to import ingestion connectors: %s", e)
    raise

# Import monitoring modules
try:
    from monitoring.volume_checks import get_volume_checks, format_volume_report  # type: ignore[import]
    from monitoring.run_logger import log_run_summary  # type: ignore[import]
except ImportError as e:
    logging.error("Failed to import monitoring modules: %s", e)
    raise


@dag(
    dag_id="marketing_data_platform",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="0 2 * * *",  # Daily at 2 AM UTC
    catchup=False,
    tags=["platform", "core", "orchestration"],
    doc_md=__doc__,
    default_args={
        "retries": 2,
        "retry_delay_seconds": 300,  # 5 minutes between retries
    },
)
def marketing_data_platform():
    """
    Main orchestration DAG for the marketing data platform.
    
    Flow:
    - google_ads_extract → meta_ads_extract → dbt_run → dbt_test
    """

    # ========== EXTRACTION PHASE ==========
    @task(task_id="extract_google_ads", retries=2)
    def extract_google_ads_task(**context) -> dict:
        """
        Extract Google Ads campaign data from raw ingestion.
        
        Config parameters:
        - start_date: ISO date string (default: 2024-01-01)
        - end_date: ISO date string (default: 2024-01-02)
        """
        conf = context.get("dag_run").conf or {}
        start_date = conf.get("start_date", "2024-01-01")
        end_date = conf.get("end_date", "2024-01-02")

        logging.info("Extracting Google Ads from %s to %s", start_date, end_date)
        result = run_google_ads(start_date=start_date, end_date=end_date)
        
        logging.info("Google Ads extraction completed: %s records", len(result))
        return {
            "source": "google_ads",
            "records": len(result),
            "start_date": start_date,
            "end_date": end_date,
        }

    @task(task_id="extract_meta_ads", retries=2)
    def extract_meta_ads_task(**context) -> dict:
        """
        Extract Meta Ads campaign data from raw ingestion.
        
        Config parameters:
        - start_date: ISO date string (default: 2024-01-01)
        - end_date: ISO date string (default: 2024-01-02)
        """
        conf = context.get("dag_run").conf or {}
        start_date = conf.get("start_date", "2024-01-01")
        end_date = conf.get("end_date", "2024-01-02")

        logging.info("Extracting Meta Ads from %s to %s", start_date, end_date)
        result = run_meta_ads(start_date=start_date, end_date=end_date)
        
        logging.info("Meta Ads extraction completed: %s records", len(result))
        return {
            "source": "meta_ads",
            "records": len(result),
            "start_date": start_date,
            "end_date": end_date,
        }

    # ========== TRANSFORMATION PHASE (dbt) ==========
    @task(task_id="dbt_run", retries=2)
    def dbt_run_task(**context) -> dict:
        """Run dbt models: staging → intermediate → marts."""
        try:
            # Adjust path based on Airflow environment
            dbt_project_path = Path(__file__).resolve().parents[1] / "dbt" / "mdp"
            
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f"""
                    cd {dbt_project_path} && \
                    dbt run \
                        --profiles-dir . \
                        --target dev \
                        --vars '{{"execution_date": "{context["ds"]}"}}' \
                        --full-refresh
                    """,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=600,
            )
            
            if result.returncode == 0:
                logging.info("dbt run completed successfully")
                return {"status": "success", "return_code": 0}
            else:
                logging.error("dbt run failed: %s", result.stderr)
                raise RuntimeError(
                    f"dbt run failed (code {result.returncode}): {result.stderr}"
                )
                
        except (subprocess.TimeoutExpired, OSError) as e:
            logging.error("Failed to run dbt: %s", e)
            raise

    @task(
        task_id="dbt_test",
        retries=1,
        trigger_rule=TriggerRule.ALL_DONE,  # Run even if dbt_run fails
    )
    def dbt_test_task(**context) -> dict:
        """Run dbt tests for data quality validation."""
        try:
            dbt_project_path = Path(__file__).resolve().parents[1] / "dbt" / "mdp"
            
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f"""
                    cd {dbt_project_path} && \
                    dbt test \
                        --profiles-dir . \
                        --target dev \
                        --vars '{{"execution_date": "{context["ds"]}"}}' 
                    """,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=600,
            )
            
            if result.returncode == 0:
                logging.info("dbt tests passed")
                return {"status": "success", "return_code": 0}
            else:
                # Tests failed but don't raise - we want summary to run anyway
                logging.warning("dbt tests had failures: %s", result.stdout)
                return {"status": "failed", "return_code": result.returncode, "message": result.stdout}
                
        except (subprocess.TimeoutExpired, OSError) as e:
            logging.error("Failed to run dbt tests: %s", e)
            return {"status": "error", "message": str(e)}

    @task(
        task_id="dbt_docs_generate",
        trigger_rule=TriggerRule.ALL_DONE,  # Generate docs even if tests fail
    )
    def dbt_docs_task() -> dict:
        """Generate dbt documentation."""
        try:
            dbt_project_path = Path(__file__).resolve().parents[1] / "dbt" / "mdp"
            
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f"cd {dbt_project_path} && dbt docs generate --profiles-dir . --target dev",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
            )
            
            if result.returncode == 0:
                logging.info("dbt docs generated successfully")
                return {"status": "success", "docs_generated": True}
            else:
                logging.warning("dbt docs generation had warnings: %s", result.stderr)
                return {"status": "completed_with_warnings", "docs_generated": True}
                
        except (subprocess.TimeoutExpired, OSError) as e:
            logging.error("Failed to generate dbt docs: %s", e)
            return {"status": "failed", "docs_generated": False, "error": str(e)}

    @task(
        task_id="volume_control_check",
        trigger_rule=TriggerRule.ALL_DONE,  # Run even if previous tasks fail
    )
    def volume_check_task() -> dict:
        """
        Execute volume control checks for all data tables.
        Validates record counts and day-over-day variance.
        """
        try:
            # Get GCP project ID from environment
            import os
            project_id = os.getenv("GCP_PROJECT_ID", "data-pipeline-platform-484814")
            
            logging.info("Starting volume control checks for project: %s", project_id)
            
            # Execute volume checks
            results = get_volume_checks(project_id=project_id)
            
            # Format and log report
            report = format_volume_report(results)
            logging.info("Volume Check Report:\n%s", report)
            
            return {
                "status": "completed",
                "overall_status": results["summary"]["overall_status"],
                "summary": results["summary"],
                "report": report,
            }
            
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Volume control check failed: %s", e)
            return {
                "status": "failed",
                "overall_status": "ERROR",
                "error": str(e),
            }

    @task(
        task_id="pipeline_summary",
        trigger_rule=TriggerRule.ALL_DONE,  # Always run to create summary
    )
    def summary_task(
        google_ads_result: dict,
        meta_ads_result: dict,
        dbt_test_result: dict,
        dbt_docs_result: dict,
        volume_check_result: dict,
        **context,
    ) -> dict:
        """
        Generate a summary of the complete pipeline run and log to BigQuery.
        Useful for monitoring and alerting.
        """
        import os
        from datetime import datetime
        
        run_date = context["ds"]
        run_id = context["run_id"]
        dag_id = context["dag"].dag_id
        execution_date = context["execution_date"]
        
        # Determine overall status
        overall_status = "success"
        error_message = None
        error_task = None
        
        # Check for failures
        if google_ads_result.get("status") == "failed":
            overall_status = "partial"
            error_task = "extract_google_ads"
            error_message = google_ads_result.get("error", "Unknown error")
        elif meta_ads_result.get("status") == "failed":
            overall_status = "partial"
            error_task = "extract_meta_ads"
            error_message = meta_ads_result.get("error", "Unknown error")
        elif not dbt_test_result.get("success", False):
            overall_status = "partial"
            error_task = "dbt_test"
            error_message = "dbt tests failed"
        elif volume_check_result.get("overall_status") == "FAIL":
            overall_status = "partial"
            error_task = "volume_check"
            error_message = "Volume checks failed"
        
        summary = {
            "run_date": run_date,
            "dag_id": dag_id,
            "run_id": run_id,
            "status": overall_status,
            "sources": {
                "google_ads": google_ads_result,
                "meta_ads": meta_ads_result,
            },
            "dbt": {
                "test": dbt_test_result,
                "docs_generation": dbt_docs_result,
            },
            "monitoring": {
                "volume_checks": volume_check_result,
            },
        }
        
        logging.info("Pipeline Summary: %s", summary)
        
        # Log to BigQuery
        try:
            project_id = os.getenv("GCP_PROJECT_ID", "data-pipeline-platform-484814")
            log_result = log_run_summary(
                project_id=project_id,
                run_id=run_id,
                dag_id=dag_id,
                run_date=run_date,
                execution_date=execution_date,
                status=overall_status,
                google_ads_result=google_ads_result,
                meta_ads_result=meta_ads_result,
                dbt_test_result=dbt_test_result,
                dbt_docs_result=dbt_docs_result,
                volume_check_result=volume_check_result,
                error_message=error_message,
                error_task=error_task,
            )
            logging.info("Run summary logged to BigQuery: %s", log_result)
            summary["bigquery_log"] = log_result
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Failed to log run summary to BigQuery: %s", e)
            summary["bigquery_log"] = {"status": "failed", "error": str(e)}
        
        return summary

    # ========== TASK DEPENDENCIES ==========
    google_extract = extract_google_ads_task()
    meta_extract = extract_meta_ads_task()
    dbt_run = dbt_run_task()
    dbt_test = dbt_test_task()
    docs = dbt_docs_task()
    volume_check = volume_check_task()
    
    # Both extractions run in parallel, then feed to dbt_run
    [google_extract, meta_extract] >> dbt_run >> dbt_test >> docs >> volume_check
    
    # Summary depends on all tasks
    summary = summary_task(
        google_ads_result=google_extract,
        meta_ads_result=meta_extract,
        dbt_test_result=dbt_test,
        dbt_docs_result=docs,
        volume_check_result=volume_check,
    )


# DAG instantiation
marketing_data_platform()
