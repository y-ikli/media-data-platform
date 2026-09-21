"""Schémas BigQuery explicites de la zone raw (source de vérité unique).

L'autodétection de schéma est volontairement écartée : un lot ne contenant que des valeurs nulles
ou entières pour une colonne décimale ferait dériver silencieusement le type d'une exécution à l'autre.
"""

from __future__ import annotations

from dataclasses import dataclass

# (nom, type BigQuery, obligatoire)
Column = tuple[str, str, bool]

COMMON_COLUMNS: list[Column] = [
    ("date", "DATE", True),
    ("campaign_id", "STRING", True),
    ("campaign_name", "STRING", False),
    ("impressions", "INT64", True),
    ("clicks", "INT64", True),
    ("conversions", "INT64", False),
    ("conversion_value", "FLOAT64", False),
]

METADATA_COLUMNS: list[Column] = [
    ("ingested_at", "TIMESTAMP", True),
    ("extract_run_id", "STRING", True),
    ("source", "STRING", True),
    ("data_mode", "STRING", True),
]

DATA_MODES = ("real", "simulated")


@dataclass(frozen=True)
class TableSpec:
    """Description d'une table raw : nom, colonnes, colonne de coût, clustering."""

    name: str
    columns: list[Column]
    spend_column: str
    cluster_by: tuple[str, ...] = ("campaign_id",)

    @property
    def column_names(self) -> list[str]:
        return [c[0] for c in self.columns]

    @property
    def required(self) -> list[str]:
        return [c[0] for c in self.columns if c[2]]

    @property
    def non_negative(self) -> list[str]:
        return [c[0] for c in self.columns if c[1] in ("INT64", "FLOAT64")]


GOOGLE_ADS = TableSpec(
    name="google_ads_campaign_daily",
    columns=[*COMMON_COLUMNS, ("cost_usd", "FLOAT64", True), *METADATA_COLUMNS],
    spend_column="cost_usd",
)

META_ADS = TableSpec(
    name="meta_ads_campaign_daily",
    columns=[
        *COMMON_COLUMNS,
        ("spend_usd", "FLOAT64", True),
        ("likes", "INT64", False),
        ("comments", "INT64", False),
        ("shares", "INT64", False),
        ("video_views", "INT64", False),
        ("page_engagement", "INT64", False),
        *METADATA_COLUMNS,
    ],
    spend_column="spend_usd",
)

TABLES = {"google_ads": GOOGLE_ADS, "meta_ads": META_ADS}
