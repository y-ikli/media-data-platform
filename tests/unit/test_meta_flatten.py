import sys
import types

import pytest

from mdp.config import ConfigError
from mdp.ingestion.meta_ads import MetaAdsConnector, flatten_insight

ROW = {
    "campaign_id": 123,
    "campaign_name": "Promo",
    "date_start": "2024-05-01",
    "impressions": "1500",
    "clicks": "42",
    "spend": "12.34",
    "actions": [
        {"action_type": "post_reaction", "value": "7"},
        {"action_type": "purchase", "value": "3"},
        {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "2"},
        {"action_type": "link_click", "value": "40"},
    ],
    "action_values": [{"action_type": "purchase", "value": "180.5"}, {"action_type": "link_click", "value": "0"}],
}


def test_types_are_normalised():
    r = flatten_insight(ROW)
    assert r["campaign_id"] == "123" and r["impressions"] == 1500 and r["spend_usd"] == 12.34 and r["date"] == "2024-05-01"


def test_conversions_and_value_sum_only_the_configured_action_types():
    r = flatten_insight(ROW)
    assert r["conversions"] == 5 and r["conversion_value"] == 180.5
    only = flatten_insight(ROW, ["offsite_conversion.fb_pixel_purchase"])
    assert only["conversions"] == 2 and only["conversion_value"] is None


def test_missing_actions_are_null_not_zero():
    """Zéro conversion et « conversion non suivie » sont deux faits différents."""
    r = flatten_insight({"campaign_id": 1, "date_start": "2024-05-01", "impressions": "1", "clicks": "0", "spend": "0"})
    assert r["conversions"] is None and r["conversion_value"] is None and r["likes"] is None


def test_engagement_actions_are_extracted():
    assert flatten_insight(ROW)["likes"] == 7


# --- connecteur réel avec un SDK factice (le SDK est un extra optionnel) ---------------------------------------


ENV = {"META_ADS_APP_ID": "a", "META_ADS_APP_SECRET": "s", "META_ADS_ACCESS_TOKEN": "t", "META_ADS_ACCOUNT_ID": "act_1"}


@pytest.fixture
def fake_sdk(monkeypatch):
    calls = {}

    class FacebookAdsApi:
        @staticmethod
        def init(*args):
            calls["init"] = args

    class AdAccount:
        def __init__(self, account_id):
            calls["account"] = account_id

        def get_insights(self, fields, params):
            calls["params"] = params
            return [ROW]

    api = types.ModuleType("facebook_business.api")
    api.FacebookAdsApi = FacebookAdsApi
    acc = types.ModuleType("facebook_business.adobjects.adaccount")
    acc.AdAccount = AdAccount
    for name, mod in {
        "facebook_business": types.ModuleType("facebook_business"),
        "facebook_business.api": api,
        "facebook_business.adobjects": types.ModuleType("facebook_business.adobjects"),
        "facebook_business.adobjects.adaccount": acc,
    }.items():
        monkeypatch.setitem(sys.modules, name, mod)
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    return calls


def test_real_mode_extracts_and_flattens(fake_sdk):
    rows = MetaAdsConnector("real").extract("2024-05-01", "2024-05-01")
    assert rows[0]["conversions"] == 5 and rows[0]["spend_usd"] == 12.34
    assert fake_sdk["init"] == ("a", "s", "t") and fake_sdk["account"] == "act_1"
    assert fake_sdk["params"]["time_increment"] == 1 and fake_sdk["params"]["level"] == "campaign"


def test_conversion_actions_are_configurable(fake_sdk, monkeypatch):
    monkeypatch.setenv("META_CONVERSION_ACTIONS", "offsite_conversion.fb_pixel_purchase")
    assert MetaAdsConnector("real").extract("2024-05-01", "2024-05-01")[0]["conversions"] == 2


def test_real_mode_fails_loudly_without_credentials(fake_sdk, monkeypatch):
    monkeypatch.delenv("META_ADS_ACCESS_TOKEN")
    with pytest.raises(ConfigError, match="META_ADS_ACCESS_TOKEN"):
        MetaAdsConnector("real")
