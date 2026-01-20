"""Connector for Meta Ads data ingestion."""
# pylint: disable=import-error

from pathlib import Path
import json

from ingestion.base import DataSourceConnector


class MetaAdsConnector(DataSourceConnector):
    """Connector for extracting raw Meta Ads data (Facebook/Instagram)."""
    
    def __init__(self):
        """Initialize the Meta Ads connector."""
        super().__init__(source_name="meta_ads")
        self.data_path = Path("/opt/airflow/data/samples/meta_ads_campaign_daily.json")
    
    def extract(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract Meta Ads data from JSON file.
        
        In production, this method would call the Meta Ads Manager API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)
        
        Returns:
            List of dictionaries containing campaign data filtered by date
        """
        with self.data_path.open(encoding="utf-8") as f:
            data = json.load(f)
        
        return [
            row
            for row in data
            if start_date <= row["date"] <= end_date
        ]


# Singleton instance of the Meta Ads connector
connector = MetaAdsConnector()


def run(start_date: str, end_date: str) -> list[dict]:
    """
    Execute the complete Meta Ads ingestion pipeline.
    
    Entry point for Airflow DAGs.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)
    
    Returns:
        List of enriched dictionaries ready for raw zone
    """
    return connector.run(start_date, end_date)
