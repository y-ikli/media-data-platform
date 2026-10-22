"""Générateur déterministe de performances publicitaires.

Chaque valeur dépend uniquement de (graine, campagne, jour) : rejouer une période redonne
exactement les mêmes lignes. L'idempotence du chargement se vérifie, et les tests sont stables.
"""

import hashlib
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from adsdata.ingestion.dates import DateWindow

type Record = dict[str, object]
type SourceBuilder = Callable[[random.Random, int, int], Record]
"""Ajoute les colonnes propres à une source (à partir du générateur, impressions, clics)."""


@dataclass(frozen=True, slots=True)
class Campaign:
    """Campagne fictive."""

    campaign_id: str
    name: str


def seeded_rng(seed: str, campaign_id: str, day: str) -> random.Random:
    """Générateur aléatoire propre à (graine, campagne, jour), stable d'une exécution à l'autre."""
    digest = hashlib.sha256(f"{seed}|{campaign_id}|{day}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))  # aléatoire non cryptographique, voulu


def generate(
    seed: str,
    campaigns: Sequence[Campaign],
    window: DateWindow,
    build: SourceBuilder,
) -> list[Record]:
    """Une ligne par campagne et par jour de ``window``.

    Garantit ``clicks <= impressions``. ``build`` ajoute les colonnes propres à la source.
    """
    rows: list[Record] = []
    for day in window.days():
        for campaign in campaigns:
            rng = seeded_rng(seed, campaign.campaign_id, day.isoformat())
            impressions = rng.randint(5_000, 100_000)
            clicks = rng.randint(50, min(2_000, impressions))
            rows.append(
                {
                    "date": day.isoformat(),
                    "campaign_id": campaign.campaign_id,
                    "campaign_name": campaign.name,
                    "impressions": impressions,
                    "clicks": clicks,
                    **build(rng, impressions, clicks),
                }
            )
    return rows
