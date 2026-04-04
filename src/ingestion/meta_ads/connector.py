"""
Meta Ads (Facebook/Instagram) data source connector.

Extracts daily campaign performance data from the Meta Marketing API and loads
it into the BigQuery raw zone (mdp_raw). Falls back to a fake API when real
credentials are not available, allowing development without a live account.
Real API extraction via facebook-business SDK is not yet implemented (see _extract_real_api).
"""
# pylint: disable=import-error

import logging
import os
from typing import Optional
from ingestion.base import DataSourceConnector
from fake_apis.meta_ads_api import get_campaign_daily

# Real API imports — only available when facebook-business is installed
try:
    from facebook_business.api import FacebookAdsApi
    META_ADS_AVAILABLE = True
except ImportError:
    META_ADS_AVAILABLE = False
    logging.warning("Meta Ads library not available, using fake API")

logger = logging.getLogger(__name__)


class MetaAdsConnector(DataSourceConnector):  # pylint: disable=too-few-public-methods
    """Connector for extracting raw Meta Ads data (Facebook/Instagram)."""

    def __init__(self, use_real_api: bool = False):
        """
        Initialize the Meta Ads connector.

        Args:
            use_real_api: If True, use real Meta Ads API. If False, use fake API.
        """
        super().__init__(source_name="meta_ads")
        self.use_real_api = use_real_api and META_ADS_AVAILABLE

        if self.use_real_api:
            logger.info("Using real Meta Ads API")
            self._api = self._init_real_api()
        else:
            logger.info("Using fake Meta Ads API")
            self._api = None

    def _init_real_api(self) -> Optional[FacebookAdsApi]:
        """Initialize the real Meta Ads API client from environment variables."""
        try:
            app_id = os.getenv("META_ADS_APP_ID")
            app_secret = os.getenv("META_ADS_APP_SECRET")
            access_token = os.getenv("META_ADS_ACCESS_TOKEN")

            if not all([app_id, app_secret, access_token]):
                logger.warning("Missing Meta Ads credentials in environment variables")
                return None

            api = FacebookAdsApi.init(app_id, app_secret, access_token)
            logger.info("Meta Ads API initialized successfully")
            return api

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Meta SDK can raise various undocumented exceptions on init failure
            logger.error("Failed to initialize Meta Ads API: %s", e)
            return None

    def extract(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract Meta Ads data.

        Uses real API if available and configured, otherwise falls back to fake API.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)

        Returns:
            List of dictionaries containing campaign data
        """
        if self.use_real_api and self._api:
            return self._extract_real_api(start_date, end_date)
        return self._extract_fake_api(start_date, end_date)

    def _extract_real_api(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract data from real Meta Ads API.

        TODO: implement real API calls using facebook-business SDK
        """
        logger.info("Extracting Meta Ads data from real API (NOT IMPLEMENTED YET)")
        logger.info("Would extract from %s to %s", start_date, end_date)
        return []

    def _extract_fake_api(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract Meta Ads data from fake API (development mode).

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)

        Returns:
            List of dictionaries containing generated campaign data
        """
        logger.info("Extracting Meta Ads data from fake API (%s to %s)", start_date, end_date)
        data = get_campaign_daily(start_date, end_date)
        logger.info("Extracted %d records from fake API", len(data))
        return data


# Singleton instance — reused by Airflow DAGs
connector = MetaAdsConnector()


def run(start_date: str, end_date: str) -> list[dict]:
    """
    Execute the complete Meta Ads ingestion pipeline.

    Pipeline: Extract → Enrich with metadata → Load to BigQuery

    Entry point for Airflow DAGs.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)

    Returns:
        List of enriched dictionaries loaded to BigQuery
    """
    return connector.run(start_date, end_date)
