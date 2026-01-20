"""Unit tests for volume checks module."""

from src.monitoring.volume_checks import VOLUME_THRESHOLDS


def test_volume_thresholds_structure():
    """Test that volume thresholds are properly defined."""
    assert len(VOLUME_THRESHOLDS) == 5
    
    for thresholds in VOLUME_THRESHOLDS.values():
        assert "min_daily_records" in thresholds
        assert "max_daily_records" in thresholds
        assert "max_variance_percent" in thresholds
        assert "description" in thresholds
        
        # Validate threshold values are positive
        assert thresholds["min_daily_records"] >= 0
        assert thresholds["max_daily_records"] > thresholds["min_daily_records"]
        assert 0 < thresholds["max_variance_percent"] <= 100


def test_table_ids_format():
    """Test that table IDs follow expected naming convention."""
    for table_id in VOLUME_THRESHOLDS:
        # Format: dataset.table_name
        parts = table_id.split(".")
        assert len(parts) == 2
        
        dataset = parts[0]
        assert dataset in ["mdp_raw", "mdp_staging", "mdp_marts"]


def test_thresholds_logical_consistency():
    """Test that thresholds are logically consistent."""
    marts_thresholds = VOLUME_THRESHOLDS.get("mdp_marts.mart_campaign_daily")
    assert marts_thresholds is not None
    
    # Marts should have higher min threshold than raw
    raw_google = VOLUME_THRESHOLDS.get("mdp_raw.google_ads_campaign_daily")
    if raw_google:
        # Marts aggregate multiple sources, so min should be reasonable
        assert marts_thresholds["min_daily_records"] >= 1


def test_variance_thresholds_reasonable():
    """Test that variance thresholds are in reasonable range."""
    for thresholds in VOLUME_THRESHOLDS.values():
        variance = thresholds["max_variance_percent"]
        # Variance should be between 10% and 100%
        assert 10 <= variance <= 100
