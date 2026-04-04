"""
Google Ads data source connector.

Extracts daily campaign performance data from the Google Ads API and loads it
into the BigQuery raw zone (mdp_raw). Falls back to a fake API when real
credentials are not available, allowing development without a live account.
Real API extraction via GAQL is not yet implemented (see _extract_real_api).
"""
# pylint: disable=import-error

import logging
import os
from typing import Optional
from ingestion.base import DataSourceConnector
from fake_apis.google_ads_api import get_campaign_daily

# Real API imports — only available when google-ads is installed
try:
    from google.ads.googleads.client import GoogleAdsClient
    GOOGLE_ADS_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_AVAILABLE = False
    logging.warning("Google Ads library not available, using fake API")

logger = logging.getLogger(__name__)


class GoogleAdsConnector(DataSourceConnector):  # pylint: disable=too-few-public-methods
    """Connector for extracting raw Google Ads data."""

    def __init__(self, use_real_api: bool = False):
        """
        Initialize the Google Ads connector.

        Args:
            use_real_api: If True, use real Google Ads API. If False, use fake API.
        """
        super().__init__(source_name="google_ads")
        self.use_real_api = use_real_api and GOOGLE_ADS_AVAILABLE

        if self.use_real_api:
            logger.info("Using real Google Ads API")
            self._client = self._init_real_client()
        else:
            logger.info("Using fake Google Ads API")
            self._client = None

    def _init_real_client(self) -> Optional[GoogleAdsClient]:
        """Initialize the real Google Ads API client from environment variables."""
        try:
            credentials = {
                "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
                "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
                "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
                "customer_id": os.getenv("GOOGLE_ADS_CUSTOMER_ID"),
            }

            if not all(credentials.values()):
                logger.warning("Missing Google Ads credentials in environment variables")
                return None

            return GoogleAdsClient.load_from_dict(credentials)

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Google Ads SDK can raise various undocumented exceptions on init failure
            logger.error("Failed to initialize Google Ads client: %s", e)
            return None

    def extract(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract Google Ads data.

        Uses real API if available and configured, otherwise falls back to fake API.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)

        Returns:
            List of dictionaries containing campaign data
        """
        if self.use_real_api and self._client:
            return self._extract_real_api(start_date, end_date)
        return self._extract_fake_api(start_date, end_date)

    def _extract_real_api(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract data from real Google Ads API.

        TODO: implement real API calls using GAQL (Google Ads Query Language)
        """
        logger.info("Extracting Google Ads data from real API (NOT IMPLEMENTED YET)")
        logger.info("Would extract from %s to %s", start_date, end_date)
        return []

    def _extract_fake_api(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract Google Ads data from fake API (development mode).

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)

        Returns:
            List of dictionaries containing generated campaign data
        """
        logger.info("Extracting Google Ads data from fake API (%s to %s)", start_date, end_date)
        data = get_campaign_daily(start_date, end_date)
        logger.info("Extracted %d records from fake API", len(data))
        return data


# Singleton instance — reused by Airflow DAGs
connector = GoogleAdsConnector()


def run(start_date: str, end_date: str) -> list[dict]:
    """
    Execute the complete Google Ads ingestion pipeline.

    Pipeline: Extract → Enrich with metadata → Load to BigQuery

    Entry point for Airflow DAGs.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)

    Returns:
        List of enriched dictionaries loaded to BigQuery
    """
    return connector.run(start_date, end_date)
