"""Fake Meta Ads API for development and testing."""

from datetime import datetime, timedelta
import random


class FakeMetaAdsAPI:
    """
    Simulates Meta Ads API (Facebook/Instagram) responses.
    
    Generates realistic campaign data for testing and development.
    """
    
    def __init__(self):
        """Initialize the fake API."""
        self.campaigns = {
            "fb_campaign_001": "Facebook - Product Showcase",
            "fb_campaign_002": "Instagram - Influencer Partnership",
            "fb_campaign_003": "Facebook - Retargeting",
            "fb_campaign_004": "Instagram - Story Ads",
            "fb_campaign_005": "Facebook - Lead Generation",
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
                # Generate realistic metrics (Meta Ads specific)
                impressions = random.randint(10000, 100000)
                clicks = random.randint(100, 1000)
                likes = random.randint(200, 2000)
                comments = random.randint(10, 200)
                shares = random.randint(5, 100)
                conversions = random.randint(10, 100)
                spend = round(random.uniform(500, 5000), 2)
                
                record = {
                    "date": date_str,
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "impressions": impressions,
                    "clicks": clicks,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "conversions": conversions,
                    "spend_usd": spend,
                    "ctr": round(clicks / impressions * 100, 2) if impressions > 0 else 0,
                    "engagement_rate": round(
                        (likes + comments + shares) / impressions * 100, 2
                    ) if impressions > 0 else 0,
                    "cpc": round(spend / clicks, 2) if clicks > 0 else 0,
                    "cpa": round(spend / conversions, 2) if conversions > 0 else 0,
                }
                data.append(record)
            
            current += timedelta(days=1)
        
        return data


# Singleton instance
meta_ads_api = FakeMetaAdsAPI()


def get_campaign_daily(start_date: str, end_date: str) -> list[dict]:
    """
    Fetch campaign daily data from fake API.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)
    
    Returns:
        List of daily campaign performance records
    """
    return meta_ads_api.get_campaign_daily_data(start_date, end_date)
