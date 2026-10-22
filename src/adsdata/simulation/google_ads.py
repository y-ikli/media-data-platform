"""API Google Ads simulée, au format de la vraie API (coûts en micros)."""

import random

from adsdata.ingestion.dates import DateWindow
from adsdata.simulation.generator import Campaign, Record, generate

SEED = "google_ads"
CURRENCY = "EUR"
MICROS_PER_UNIT = 1_000_000
AVERAGE_ORDER_VALUE = 60.0

CAMPAIGNS: tuple[Campaign, ...] = (
    Campaign("gads_001", "Search - Marque"),
    Campaign("gads_002", "Search - Concurrents"),
    Campaign("gads_003", "Shopping - Catalogue"),
    Campaign("gads_004", "Performance Max - Soldes"),
    Campaign("gads_005", "YouTube - Notoriété"),
)


def _build(rng: random.Random, impressions: int, clicks: int) -> Record:
    # Conversions à virgule : Google répartit une conversion entre plusieurs clics.
    conversions = round(rng.uniform(0, clicks / 15), 2)
    cost = rng.uniform(clicks * 0.3, clicks * 1.5)
    return {
        "conversions": conversions,
        "conversion_value": round(conversions * rng.uniform(0.6, 1.4) * AVERAGE_ORDER_VALUE, 2),
        "cost_micros": round(cost * MICROS_PER_UNIT),
        "currency_code": CURRENCY,
    }


def campaign_daily(window: DateWindow) -> list[Record]:
    """Lignes journalières simulées par campagne, pour chaque jour de ``window``."""
    return generate(SEED, CAMPAIGNS, window, _build)
