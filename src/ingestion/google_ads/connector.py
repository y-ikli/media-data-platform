"""Connector for Google Ads data ingestion."""
# pylint: disable=import-error

import logging
from ingestion.base import DataSourceConnector
from fake_apis.google_ads_api import get_campaign_daily

logger = logging.getLogger(__name__)


class GoogleAdsConnector(DataSourceConnector):
    """Connector for extracting raw Google Ads data."""
    
    def __init__(self):
        """Initialize the Google Ads connector."""
        super().__init__(source_name="google_ads")
    
    def extract(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract Google Ads data from fake API.
        
        In production, this method would call the Google Ads API.
        The fake API generates realistic test data.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)
        
        Returns:
            List of dictionaries containing campaign data filtered by date
        """
        logger.info("Extracting Google Ads data from %s to %s", start_date, end_date)
        data = get_campaign_daily(start_date, end_date)
        logger.info("Extracted %d records from fake API", len(data))
        return data

# Singleton instance of the Google Ads connector
connector = GoogleAdsConnector()


def run(start_date: str, end_date: str) -> list[dict]:
    """
    Execute the complete Google Ads ingestion pipeline.
    
    Pipeline: Extract (fake API) → Enrich → Load to BigQuery
    
    Entry point for Airflow DAGs.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)
    
    Returns:
        List of enriched dictionaries loaded to BigQuery
    """
    return connector.run(start_date, end_date)