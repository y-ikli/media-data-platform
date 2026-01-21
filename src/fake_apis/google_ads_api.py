"""Fake Google Ads API for development and testing."""

from datetime import datetime, timedelta
import random


class FakeGoogleAdsAPI:
    """
    Simulates Google Ads API responses.
    
    Generates realistic campaign data for testing and development.
    """
    
    def __init__(self):
        """Initialize the fake API."""
        self.campaigns = {
            "campaign_001": "Summer Sale Campaign",
            "campaign_002": "Black Friday Promotion",
            "campaign_003": "Q1 Brand Awareness",
            "campaign_004": "Product Launch",
            "campaign_005": "Holiday Season",
        }
    
    def get_campaign_daily_data(self, start_date: str, end_date: str) -> list[dict]:
        """
        Get fake daily campaign data between two dates.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)
        
        Returns:
            List of daily campaign performance records
        """
        data = []
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start
        
        # Generate data for each day and each campaign
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            
            for campaign_id, campaign_name in self.campaigns.items():
                # Generate realistic metrics
                impressions = random.randint(5000, 50000)
                clicks = random.randint(50, 500)
                conversions = random.randint(5, 50)
                cost = round(random.uniform(100, 1000), 2)
                
                record = {
                    "date": date_str,
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "cost_usd": cost,
                    "ctr": round(clicks / impressions * 100, 2) if impressions > 0 else 0,
                    "conversion_rate": round(conversions / clicks * 100, 2) if clicks > 0 else 0,
                    "cpc": round(cost / clicks, 2) if clicks > 0 else 0,
                    "cpa": round(cost / conversions, 2) if conversions > 0 else 0,
                }
                data.append(record)
            
            current += timedelta(days=1)
        
        return data


# Singleton instance
google_ads_api = FakeGoogleAdsAPI()


def get_campaign_daily(start_date: str, end_date: str) -> list[dict]:
    """
    Fetch campaign daily data from fake API.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)
    
    Returns:
        List of daily campaign performance records
    """
    return google_ads_api.get_campaign_daily_data(start_date, end_date)
