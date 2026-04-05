"""
Fake Google Ads API for development and testing.

Generates realistic daily campaign performance data without requiring
real Google Ads credentials. Only raw metrics are returned — KPI calculations
(CTR, CPA, CPC, etc.) are handled downstream in dbt.
"""

from datetime import datetime, timedelta
import random


class FakeGoogleAdsAPI:  # pylint: disable=too-few-public-methods,duplicate-code
    """Simulates Google Ads API responses with randomly generated campaign data."""

    def __init__(self):
        """Initialize with a fixed set of fictional campaigns."""
        self.campaigns = {
            "campaign_001": "Summer Sale Campaign",
            "campaign_002": "Black Friday Promotion",
            "campaign_003": "Q1 Brand Awareness",
            "campaign_004": "Product Launch",
            "campaign_005": "Holiday Season",
        }

    def get_campaign_daily_data(self, start_date: str, end_date: str) -> list[dict]:
        """
        Generate fake daily campaign data between two dates.

        Returns one record per campaign per day with raw metrics only.
        No derived KPIs — those are computed in dbt.

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
                    "impressions": random.randint(5000, 50000),
                    "clicks": random.randint(50, 500),
                    "conversions": random.randint(5, 50),
                    "cost_usd": round(random.uniform(100, 1000), 2),
                }
                data.append(record)

            current += timedelta(days=1)

        return data


# Singleton instance
google_ads_api = FakeGoogleAdsAPI()


def get_campaign_daily(start_date: str, end_date: str) -> list[dict]:
    """
    Fetch daily campaign data from fake Google Ads API.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (inclusive)

    Returns:
        List of daily campaign performance records
    """
    return google_ads_api.get_campaign_daily_data(start_date, end_date)
