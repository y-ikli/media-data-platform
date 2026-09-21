"""Générateur déterministe de performances publicitaires simulées.

Chaque valeur dépend uniquement de (graine, campagne, date) : rejouer une plage redonne exactement
les mêmes lignes, ce qui rend l'ingestion reproductible et les tests stables.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Callable, Iterator
from datetime import date, timedelta

Record = dict[str, object]


def _rng(seed: str, campaign_id: str, day: date) -> random.Random:
    digest = hashlib.sha256(f"{seed}|{campaign_id}|{day.isoformat()}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def days(start: str, end: str) -> Iterator[date]:
    current, last = date.fromisoformat(start), date.fromisoformat(end)
    while current <= last:
        yield current
        current += timedelta(days=1)


def generate(
    seed: str,
    campaigns: dict[str, str],
    start: str,
    end: str,
    build: Callable[[random.Random, int, int], Record],
) -> list[Record]:
    """Une ligne par campagne et par jour ; ``build(rng, impressions, clicks)`` ajoute les colonnes propres à la source.

    Invariant garanti : ``clicks <= impressions``.
    """
    rows: list[Record] = []
    for day in days(start, end):
        for campaign_id, campaign_name in campaigns.items():
            rng = _rng(seed, campaign_id, day)
            impressions = rng.randint(5_000, 100_000)
            clicks = rng.randint(50, min(1_000, impressions))
            rows.append(
                {
                    "date": day.isoformat(),
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "impressions": impressions,
                    "clicks": clicks,
                    **build(rng, impressions, clicks),
                }
            )
    return rows
