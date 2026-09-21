"""API Meta Ads simulée (campagnes fictives, données déterministes)."""

from __future__ import annotations

from mdp.fake_apis.generator import Record, generate

CAMPAIGNS = {
    "meta_camp_001": "Brand Awareness - FR",
    "meta_camp_002": "Product Launch Q1",
    "meta_camp_003": "Retargeting - Cart Abandoners",
    "meta_camp_004": "Lookalike - Newsletter",
}


def _build(rng, impressions: int, clicks: int) -> Record:
    conversions = rng.randint(0, max(1, clicks // 12))
    return {
        "conversions": conversions,
        "conversion_value": round(conversions * rng.uniform(0.5, 1.5) * 55.0, 2),
        "spend_usd": round(rng.uniform(50, 800), 2),
        "likes": rng.randint(0, impressions // 40),
        "comments": rng.randint(0, impressions // 400),
        "shares": rng.randint(0, impressions // 800),
        "video_views": rng.randint(0, impressions // 5),
        "page_engagement": rng.randint(0, impressions // 20),
    }


def get_campaign_daily(start_date: str, end_date: str) -> list[dict]:
    """Lignes journalières simulées de ``start_date`` à ``end_date`` (incluses)."""
    return generate("meta_ads", CAMPAIGNS, start_date, end_date, _build)
