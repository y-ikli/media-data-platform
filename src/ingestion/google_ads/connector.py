"""Connector for Google Ads data ingestion."""
# pylint: disable=import-error

from pathlib import Path
import json

from ingestion.base import DataSourceConnector


class GoogleAdsConnector(DataSourceConnector):
    """Connector for extracting raw Google Ads data."""
    
    def __init__(self):
        """Initialize the Google Ads connector."""
        super().__init__(source_name="google_ads")
        self.data_path = Path("/opt/airflow/data/samples/google_ads_campaign_daily.json")
    
    def extract(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract Google Ads data from JSON file.
        
        In production, this method would call the Google Ads Client API.
        
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


# Singleton instance of the Google Ads connector
connector = GoogleAdsConnector()


def run(start_date: str, end_date: str) -> list[dict]:
    """
    Execute the complete Google Ads ingestion pipeline.
    
    Entry point for Airflow DAGs.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)
    
    Returns:
        List of enriched dictionaries ready for raw zone
    """
    return connector.run(start_date, end_date)