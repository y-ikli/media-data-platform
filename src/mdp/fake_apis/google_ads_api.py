"""API Google Ads simulée (campagnes fictives, données déterministes)."""

from __future__ import annotations

from mdp.fake_apis.generator import Record, generate

CAMPAIGNS = {
    "campaign_001": "Summer Sale Campaign",
    "campaign_002": "Black Friday Promotion",
    "campaign_003": "Q1 Brand Awareness",
    "campaign_004": "Product Launch",
    "campaign_005": "Holiday Season",
}
AVERAGE_ORDER_VALUE_USD = 60.0


def _build(rng, _impressions: int, clicks: int) -> Record:
    conversions = rng.randint(0, max(1, clicks // 10))
    return {
        "conversions": conversions,
        "conversion_value": round(conversions * rng.uniform(0.6, 1.4) * AVERAGE_ORDER_VALUE_USD, 2),
        "cost_usd": round(rng.uniform(100, 1000), 2),
    }


def get_campaign_daily(start_date: str, end_date: str) -> list[dict]:
    """Lignes journalières simulées de ``start_date`` à ``end_date`` (incluses)."""
    return generate("google_ads", CAMPAIGNS, start_date, end_date, _build)
