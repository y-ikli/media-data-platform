"""
Deduplicate BigQuery raw tables.

Keeps the most recent row per (date, campaign_id) based on ingested_at.
Safe to run multiple times — idempotent.

Usage:
    python scripts/deduplicate_raw.py
    python scripts/deduplicate_raw.py --project my-project
    python scripts/deduplicate_raw.py --tables meta_ads_campaign_daily
"""

import argparse
import logging

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

RAW_TABLES = [
    "meta_ads_campaign_daily",
    "google_ads_campaign_daily",
]


def deduplicate_table(client: bigquery.Client, project_id: str, table: str) -> int:
    """Deduplicate a raw table, keeping the most recent row per (date, campaign_id)."""
    full_table = f"`{project_id}.mdp_raw.{table}`"
    query = f"""
    CREATE OR REPLACE TABLE {full_table} AS
    SELECT * EXCEPT(rn)
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY date, campaign_id
                ORDER BY ingested_at DESC
            ) AS rn
        FROM {full_table}
    )
    WHERE rn = 1
    """
    job = client.query(query)
    job.result()
    table_ref = client.get_table(f"{project_id}.mdp_raw.{table}")
    return table_ref.num_rows


def main():
    parser = argparse.ArgumentParser(description="Deduplicate BigQuery raw tables")
    parser.add_argument("--project", default="media-data-platform", help="GCP project ID")
    parser.add_argument("--tables", nargs="+", default=RAW_TABLES, help="Tables to deduplicate")
    args = parser.parse_args()

    client = bigquery.Client(project=args.project)

    for table in args.tables:
        logger.info("Deduplicating %s ...", table)
        rows = deduplicate_table(client, args.project, table)
        logger.info("  → %d rows remaining", rows)

    logger.info("Done.")


if __name__ == "__main__":
    main()