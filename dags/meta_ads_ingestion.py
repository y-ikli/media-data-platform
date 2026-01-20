"""
DAG for raw Meta Ads data ingestion (Facebook/Instagram).

This DAG executes the ingestion script located in the `ingestion.meta_ads` module.
It is configured to be triggered manually.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pendulum
from airflow.decorators import dag, task

# Add 'src' folder to PYTHONPATH to enable local module imports
_SRC_DIR = (Path(__file__).resolve().parents[1] / "src").as_posix()
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Deferred or protected import to avoid errors if path is not yet configured
try:
    from ingestion.meta_ads.connector import run
except ImportError as e:
    logging.error("Failed to import Meta Ads connector: %s", e)
    raise


@dag(
    dag_id="meta_ads_ingestion_raw",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    tags=["ingestion", "raw", "meta_ads"],
    doc_md=__doc__,
)
def meta_ads_ingestion_pipeline():
    """Meta Ads data ingestion DAG."""
    
    @task(task_id="ingest_meta_ads_raw")
    def run_ingestion_task(**context) -> list[dict]:
        """
        Execute Meta Ads ingestion logic.
        
        Start and end dates can be overridden via Run configuration
        (ex: {"start_date": "2024-02-01"}).
        """
        # Retrieve optional configuration provided at trigger time
        conf = context.get("dag_run").conf or {}
        
        start_date = conf.get("start_date", "2024-01-01")
        end_date = conf.get("end_date", "2024-01-02")

        logging.info("Starting Meta Ads ingestion from %s to %s", start_date, end_date)

        return run(start_date=start_date, end_date=end_date)

    # Invoke the task
    run_ingestion_task()


# DAG instantiation
meta_ads_ingestion_pipeline()
