"""API Meta Ads simulée, déjà aplatie au format de la table raw."""

import random

from adsdata.ingestion.dates import DateWindow
from adsdata.simulation.generator import Campaign, Record, generate

SEED = "meta_ads"
CURRENCY = "EUR"
AVERAGE_ORDER_VALUE = 55.0

CAMPAIGNS: tuple[Campaign, ...] = (
    Campaign("meta_001", "Notoriété - France"),
    Campaign("meta_002", "Lancement produit"),
    Campaign("meta_003", "Retargeting - Paniers abandonnés"),
    Campaign("meta_004", "Audience similaire - Newsletter"),
)


def _build(rng: random.Random, impressions: int, clicks: int) -> Record:
    conversions = rng.randint(0, max(1, clicks // 20))
    return {
        "conversions": float(conversions),
        "conversion_value": round(conversions * rng.uniform(0.5, 1.5) * AVERAGE_ORDER_VALUE, 2),
        "spend": round(rng.uniform(clicks * 0.2, clicks * 1.2), 2),
        "account_currency": CURRENCY,
        "likes": rng.randint(0, impressions // 40),
        "comments": rng.randint(0, impressions // 400),
        "shares": rng.randint(0, impressions // 800),
        "video_views": rng.randint(0, impressions // 5),
        "page_engagement": rng.randint(0, impressions // 20),
    }


def campaign_daily(window: DateWindow) -> list[Record]:
    """Lignes journalières simulées par campagne, pour chaque jour de ``window``."""
    return generate(SEED, CAMPAIGNS, window, _build)
