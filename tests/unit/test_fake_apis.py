"""Tests for fake APIs.

# pylint: disable=unused-import
# Add src to PYTHONPATH to fix relative imports in VS Code, pytest, pylint, etc.
"""
from fake_apis.google_ads_api import get_campaign_daily as get_google_ads
from fake_apis.meta_ads_api import get_campaign_daily as get_meta_ads


class TestGoogleAdsAPI:
    """Test fake Google Ads API."""
    
    def test_get_campaign_daily_returns_list(self):
        """Test that API returns a list of records."""
        result = get_google_ads("2024-01-01", "2024-01-03")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_campaign_daily_has_required_fields(self):
        """Test that records have required fields."""
        result = get_google_ads("2024-01-01", "2024-01-01")
        assert len(result) > 0
        
        required_fields = [
            "date", "campaign_id", "campaign_name", "impressions",
            "clicks", "conversions", "cost_usd"
        ]
        
        for record in result:
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
    
    def test_get_campaign_daily_date_filtering(self):
        """Test that date filtering works."""
        result = get_google_ads("2024-01-01", "2024-01-01")
        assert all(record["date"] == "2024-01-01" for record in result)


class TestMetaAdsAPI:
    """Test fake Meta Ads API."""
    
    def test_get_campaign_daily_returns_list(self):
        """Test that API returns a list of records."""
        result = get_meta_ads("2024-01-01", "2024-01-03")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_campaign_daily_has_required_fields(self):
        """Test that records have required fields."""
        result = get_meta_ads("2024-01-01", "2024-01-01")
        assert len(result) > 0
        
        required_fields = [
            "date", "campaign_id", "campaign_name", "impressions",
            "clicks", "conversions", "spend_usd"
        ]
        
        for record in result:
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
    
    def test_get_campaign_daily_meta_specific_fields(self):
        """Test Meta Ads specific fields."""
        result = get_meta_ads("2024-01-01", "2024-01-01")
        assert len(result) > 0
        
        meta_fields = ["likes", "comments", "shares", "engagement_rate"]
        
        for record in result:
            for field in meta_fields:
                assert field in record, f"Missing Meta field: {field}"
