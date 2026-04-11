"""
BigQuery connection test script.

Usage:
    python scripts/test_bigquery.py
    python scripts/test_bigquery.py --project media-data-platform
    python scripts/test_bigquery.py --project media-data-platform --datasets
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test BigQuery connection.")
    parser.add_argument(
        "--project",
        default=os.getenv("GCP_PROJECT_ID", "media-data-platform"),
        help="GCP project ID (default: GCP_PROJECT_ID env var)",
    )
    parser.add_argument(
        "--datasets",
        action="store_true",
        help="List datasets in the project",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        from google.cloud import bigquery
    except ImportError:
        print("google-cloud-bigquery not installed. Run: uv sync")
        sys.exit(1)

    print(f"Connecting to project: {args.project}")
    print(f"Credentials: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'not set (using ADC)')}")
    print()

    try:
        client = bigquery.Client(project=args.project)
        print(f"OK — connected to: {client.project}")
        print(f"Credentials type: {type(client._credentials).__name__}")
    except Exception as e:
        print(f"FAILED — {e}")
        sys.exit(1)

    if args.datasets:
        print()
        print("Datasets:")
        datasets = list(client.list_datasets())
        if datasets:
            for ds in datasets:
                print(f"  - {ds.dataset_id}")
        else:
            print("  (none — run setup_bigquery.sh to create them)")


if __name__ == "__main__":
    main()