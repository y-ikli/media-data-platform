"""
Meta Ads ingestion script.

Extracts daily campaign performance data from the Meta Ads API
and loads it into the BigQuery raw zone (mdp_raw.meta_ads_campaign_daily).

Usage:
    python scripts/ingest_meta_ads.py --start 2023-04-06 --end 2025-12-31
    python scripts/ingest_meta_ads.py --start 2024-01-01 --end 2024-12-31 --fake

Requirements:
    - META_ADS_APP_ID, META_ADS_APP_SECRET, META_ADS_ACCESS_TOKEN, META_ADS_ACCOUNT_ID
      must be set in .env or as environment variables (real API mode only)
    - GOOGLE_APPLICATION_CREDENTIALS must point to a valid GCP service account key
"""

import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src/ to path so ingestion modules can be imported
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract Meta Ads campaign data and load to BigQuery raw zone."
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="End date in YYYY-MM-DD format (inclusive)",
    )
    parser.add_argument(
        "--fake",
        action="store_true",
        default=False,
        help="Use fake API instead of real Meta Ads API (for testing)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the Meta Ads ingestion pipeline."""
    args = parse_args()

    use_real_api = not args.fake
    mode = "real API" if use_real_api else "fake API"

    logger.info("Starting Meta Ads ingestion")
    logger.info("  Period : %s -> %s", args.start, args.end)
    logger.info("  Mode   : %s", mode)

    from ingestion.meta_ads.connector import MetaAdsConnector  # pylint: disable=import-outside-toplevel,import-error

    connector = MetaAdsConnector(use_real_api=use_real_api)
    result = connector.run(args.start, args.end)

    logger.info("Ingestion completed")
    logger.info("  Rows written     : %d", len(result))
    if result:
        logger.info("  Period covered   : %s -> %s", result[0]["date"], result[-1]["date"])
        logger.info("  Unique campaigns : %d", len({r["campaign_id"] for r in result}))
        logger.info("  Total spend      : %.2f USD", sum(r.get("spend_usd", 0) for r in result))


if __name__ == "__main__":
    main()
