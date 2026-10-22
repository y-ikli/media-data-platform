import sys
import types
from datetime import date

import pytest

from adsdata.config import ConfigError
from adsdata.ingestion.connectors import CONNECTORS
from adsdata.ingestion.connectors.google_ads import GoogleAdsConnector
from adsdata.ingestion.connectors.meta_ads import (
    DEFAULT_CONVERSION_ACTIONS,
    GraphApiInsightsClient,
    MetaAdsConnector,
    conversion_actions_from_env,
    flatten_insight,
)
from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.schemas import DataMode

WEEK = DateWindow(date(2026, 10, 1), date(2026, 10, 7))

INSIGHT = {
    "date_start": "2026-10-01",
    "date_stop": "2026-10-01",
    "campaign_id": "120200000000001",
    "campaign_name": "Notoriété",
    "account_currency": "EUR",
    "impressions": "1500",
    "clicks": "42",
    "spend": "12.34",
    "actions": [
        {"action_type": "post_reaction", "value": "7"},
        {"action_type": "purchase", "value": "3"},
        {"action_type": "omni_purchase", "value": "4"},
        {"action_type": "video_view", "value": "120"},
    ],
    "action_values": [
        {"action_type": "purchase", "value": "90.5"},
        {"action_type": "omni_purchase", "value": "110.0"},
    ],
}


class FakeInsights:
    def __init__(self, insights):
        self.insights = insights
        self.windows = []

    def fetch(self, window):
        self.windows.append(window)
        return iter(self.insights)


def test_registry_lists_both_sources():
    assert set(CONNECTORS) == {"google_ads", "meta_ads"}
    with pytest.raises(TypeError):
        CONNECTORS["autre"] = GoogleAdsConnector  # type: ignore[index]


def test_google_ads_real_mode_is_refused():
    with pytest.raises(NotImplementedError, match="simulated"):
        GoogleAdsConnector(DataMode.REAL)


@pytest.mark.parametrize("connector_cls", [GoogleAdsConnector, MetaAdsConnector])
def test_simulated_extraction_passes_the_data_contract(connector_cls):
    reports = connector_cls(DataMode.SIMULATED).run(WEEK, dry_run=True)

    assert reports[0].extracted_rows > 0
    assert reports[0].data_mode == "simulated"


def test_flatten_converts_texts_and_picks_one_conversion_type():
    row = flatten_insight(INSIGHT)

    assert row == {
        "date": "2026-10-01",
        "campaign_id": "120200000000001",
        "campaign_name": "Notoriété",
        "impressions": 1500,
        "clicks": 42,
        "conversions": 4.0,
        "conversion_value": 110.0,
        "spend": 12.34,
        "account_currency": "EUR",
        "likes": 7,
        "comments": None,
        "shares": None,
        "video_views": 120,
        "page_engagement": None,
    }


def test_flatten_uses_the_configured_conversion_types():
    row = flatten_insight(INSIGHT, conversion_actions=("purchase",))

    assert (row["conversions"], row["conversion_value"]) == (3.0, 90.5)


def test_flatten_without_actions_leaves_conversions_empty():
    insight = {k: v for k, v in INSIGHT.items() if k not in ("actions", "action_values")}

    row = flatten_insight(insight)

    assert row["conversions"] is None
    assert row["likes"] is None


def test_flatten_ignores_malformed_actions():
    insight = {**INSIGHT, "actions": [{"value": "3"}, "texte"], "action_values": "absent"}

    assert flatten_insight(insight)["conversions"] is None


def test_meta_real_mode_reads_the_insights_client():
    client = FakeInsights([INSIGHT])
    connector = MetaAdsConnector(DataMode.REAL, client=client)

    rows = connector.extract(WEEK)

    assert client.windows == [WEEK]
    assert rows == [flatten_insight(INSIGHT)]


def test_meta_real_mode_without_credentials_is_an_error(monkeypatch):
    monkeypatch.delenv("META_ADS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("META_ADS_ACCOUNT_ID", raising=False)

    with pytest.raises(ConfigError, match="META_ADS_ACCESS_TOKEN"):
        MetaAdsConnector(DataMode.REAL)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", DEFAULT_CONVERSION_ACTIONS),
        ("purchase", ("purchase",)),
        (" lead , purchase ,", ("lead", "purchase")),
    ],
)
def test_conversion_actions_from_env(raw, expected):
    assert conversion_actions_from_env({"META_CONVERSION_ACTIONS": raw}) == expected


@pytest.fixture
def fake_facebook_sdk(monkeypatch):
    """Remplace la bibliothèque facebook-business par un faux, sans réseau."""
    calls = {}

    class FacebookAdsApi:
        @staticmethod
        def init(**kwargs):
            calls["init"] = kwargs

    class AdAccount:
        def __init__(self, account_id):
            calls["account"] = account_id

        def get_insights(self, fields, params):
            calls["fields"], calls["params"] = fields, params
            return [INSIGHT]

    api = types.ModuleType("facebook_business.api")
    api.FacebookAdsApi = FacebookAdsApi
    adaccount = types.ModuleType("facebook_business.adobjects.adaccount")
    adaccount.AdAccount = AdAccount
    monkeypatch.setitem(sys.modules, "facebook_business.api", api)
    monkeypatch.setitem(sys.modules, "facebook_business.adobjects.adaccount", adaccount)
    return calls


def test_graph_api_client_requests_daily_campaign_insights(fake_facebook_sdk):
    env = {"META_ADS_ACCESS_TOKEN": "jeton", "META_ADS_ACCOUNT_ID": "123", "META_ADS_APP_ID": ""}

    client = GraphApiInsightsClient.from_env(env)
    insights = list(client.fetch(WEEK))

    assert insights == [INSIGHT]
    assert fake_facebook_sdk["init"] == {
        "app_id": None,
        "app_secret": None,
        "access_token": "jeton",
    }
    assert fake_facebook_sdk["account"] == "act_123"
    assert fake_facebook_sdk["params"] == {
        "level": "campaign",
        "time_increment": 1,
        "time_range": {"since": "2026-10-01", "until": "2026-10-07"},
    }
    assert "account_currency" in fake_facebook_sdk["fields"]


def test_graph_api_client_keeps_an_act_prefix(fake_facebook_sdk):
    client = GraphApiInsightsClient("jeton", "act_123")

    assert client.account_id == "act_123"


def test_graph_api_client_without_the_meta_option(monkeypatch):
    monkeypatch.setitem(sys.modules, "facebook_business.api", None)

    with pytest.raises(ConfigError, match="extra meta"):
        GraphApiInsightsClient("jeton", "123")
