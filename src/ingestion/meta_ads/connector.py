"""Connector for Meta Ads data ingestion."""
# pylint: disable=import-error

import logging
from ingestion.base import DataSourceConnector
from fake_apis.meta_ads_api import get_campaign_daily

logger = logging.getLogger(__name__)


class MetaAdsConnector(DataSourceConnector):
    """Connector for extracting raw Meta Ads data (Facebook/Instagram)."""
    
    def __init__(self):
        """Initialize the Meta Ads connector."""
        super().__init__(source_name="meta_ads")
    
    def extract(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract Meta Ads data from fake API.
        
        In production, this method would call the Meta Ads Manager API.
        The fake API generates realistic test data.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)
        
        Returns:
            List of dictionaries containing campaign data filtered by date
        """
        logger.info("Extracting Meta Ads data from %s to %s", start_date, end_date)
        data = get_campaign_daily(start_date, end_date)
        logger.info("Extracted %d records from fake API", len(data))
        return data

# Singleton instance of the Meta Ads connector
connector = MetaAdsConnector()


def run(start_date: str, end_date: str) -> list[dict]:
    """
    Execute the complete Meta Ads ingestion pipeline.
    
    Pipeline: Extract (fake API) → Enrich → Load to BigQuery
    
    Entry point for Airflow DAGs.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)
    
    Returns:
        List of enriched dictionaries loaded to BigQuery
    """
    return connector.run(start_date, end_date)