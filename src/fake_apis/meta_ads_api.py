"""
Fake Meta Ads API for development and testing.

Generates realistic daily campaign performance data without requiring
real Meta Ads credentials. Only raw metrics are returned — KPI calculations
(CTR, CPA, CPC, etc.) are handled downstream in dbt.
"""

from datetime import datetime, timedelta
import random


class FakeMetaAdsAPI:  # pylint: disable=too-few-public-methods,duplicate-code
    """Simulates Meta Ads API (Facebook/Instagram) responses with generated campaign data."""

    def __init__(self):
        """Initialize with a fixed set of fictional campaigns."""
        self.campaigns = {
            "fb_campaign_001": "Facebook - Product Showcase",
            "fb_campaign_002": "Instagram - Influencer Partnership",
            "fb_campaign_003": "Facebook - Retargeting",
            "fb_campaign_004": "Instagram - Story Ads",
            "fb_campaign_005": "Facebook - Lead Generation",
        }

    def get_campaign_daily_data(self, start_date: str, end_date: str) -> list[dict]:
        """
        Generate fake daily campaign data between two dates.

        Returns one record per campaign per day with raw metrics only.
        No derived KPIs — those are computed in dbt.
        Meta-specific engagement metrics (likes, comments, shares) are included
        as raw signals, not computed ratios.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)

        Returns:
            List of daily campaign performance records
        """
        data = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")

            for campaign_id, campaign_name in self.campaigns.items():
                record = {
                    "date": date_str,
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "impressions": random.randint(10000, 100000),
                    "clicks": random.randint(100, 1000),
                    "conversions": random.randint(10, 100),
                    "spend_usd": round(random.uniform(500, 5000), 2),
                    "likes": random.randint(200, 2000),
                    "comments": random.randint(10, 200),
                    "shares": random.randint(5, 100),
                }
                data.append(record)

            current += timedelta(days=1)

        return data


# Singleton instance
meta_ads_api = FakeMetaAdsAPI()


def get_campaign_daily(start_date: str, end_date: str) -> list[dict]:
    """
    Fetch daily campaign data from fake Meta Ads API.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)

    Returns:
        List of daily campaign performance records
    """
    return meta_ads_api.get_campaign_daily_data(start_date, end_date)
