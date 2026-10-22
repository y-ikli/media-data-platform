"""Schémas des tables de la zone raw : source de vérité unique pour la validation et BigQuery.

Le schéma est déclaré ici et jamais déduit par BigQuery : la détection automatique type les
colonnes d'après le lot reçu, et peut changer d'une exécution à l'autre.

Ajouter une source = déclarer un ``TableSpec`` et l'enregistrer dans ``TABLE_SPECS``.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

MAX_CLUSTERING_COLUMNS = 4  # limite fixée par BigQuery


class BigQueryType(StrEnum):
    """Types BigQuery utilisés par la zone raw."""

    DATE = "DATE"
    FLOAT64 = "FLOAT64"
    INT64 = "INT64"
    STRING = "STRING"
    TIMESTAMP = "TIMESTAMP"


class DataMode(StrEnum):
    """Origine des données : API réelle ou générateur."""

    REAL = "real"
    SIMULATED = "simulated"


@dataclass(frozen=True, slots=True)
class Column:
    """Colonne d'une table raw."""

    name: str
    bq_type: BigQueryType
    required: bool = False
    allowed_values: frozenset[str] | None = None

    @property
    def is_numeric(self) -> bool:
        """Indique si la colonne contient des nombres."""
        return self.bq_type in (BigQueryType.INT64, BigQueryType.FLOAT64)


@dataclass(frozen=True, slots=True)
class TableSpec:
    """Description complète d'une table raw.

    La cohérence est vérifiée à la création : une erreur de déclaration apparaît à l'import du
    module, pas au premier chargement.
    """

    name: str
    columns: tuple[Column, ...]
    partition_field: str = "date"
    cluster_by: tuple[str, ...] = ("campaign_id",)
    unique_key: tuple[str, ...] = ("date", "campaign_id")

    def __post_init__(self) -> None:
        """Vérifie que la déclaration est cohérente."""
        names = [column.name for column in self.columns]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"{self.name} : colonnes en double {duplicates}")

        by_name = {column.name: column for column in self.columns}
        partition = by_name.get(self.partition_field)
        if partition is None or partition.bq_type is not BigQueryType.DATE:
            raise ValueError(f"{self.name} : la partition doit être une colonne DATE existante")
        if len(self.cluster_by) > MAX_CLUSTERING_COLUMNS:
            raise ValueError(
                f"{self.name} : {MAX_CLUSTERING_COLUMNS} colonnes de clustering au plus"
            )
        for label, fields in (("clustering", self.cluster_by), ("clé unique", self.unique_key)):
            unknown = sorted(set(fields) - by_name.keys())
            if unknown:
                raise ValueError(f"{self.name} : colonnes de {label} inconnues {unknown}")

    @property
    def column_names(self) -> tuple[str, ...]:
        """Noms des colonnes, dans l'ordre de la table."""
        return tuple(column.name for column in self.columns)

    def column(self, name: str) -> Column:
        """Renvoie la colonne ``name`` ; lève ``KeyError`` si elle n'existe pas."""
        for column in self.columns:
            if column.name == name:
                return column
        raise KeyError(f"{self.name} : colonne inconnue {name!r}")


COMMON_COLUMNS: tuple[Column, ...] = (
    Column("date", BigQueryType.DATE, required=True),
    Column("campaign_id", BigQueryType.STRING, required=True),
    Column("campaign_name", BigQueryType.STRING),
    Column("impressions", BigQueryType.INT64, required=True),
    Column("clicks", BigQueryType.INT64, required=True),
    Column("conversions", BigQueryType.FLOAT64),
    Column("conversion_value", BigQueryType.FLOAT64),
)
"""Colonnes présentes dans toutes les sources (grain : une campagne, un jour)."""

AUDIT_COLUMNS: tuple[Column, ...] = (
    Column("ingested_at", BigQueryType.TIMESTAMP, required=True),
    Column("extract_run_id", BigQueryType.STRING, required=True),
    Column("source", BigQueryType.STRING, required=True),
    Column(
        "data_mode",
        BigQueryType.STRING,
        required=True,
        allowed_values=frozenset(mode.value for mode in DataMode),
    ),
)
"""Colonnes de traçabilité, ajoutées par l'ingestion à chaque ligne."""

GOOGLE_ADS = TableSpec(
    name="google_ads_campaign_daily",
    columns=(
        *COMMON_COLUMNS,
        # Comme l'API Google Ads : coût en millionièmes de la devise du compte.
        Column("cost_micros", BigQueryType.INT64, required=True),
        Column("currency_code", BigQueryType.STRING, required=True),
        *AUDIT_COLUMNS,
    ),
)

META_ADS = TableSpec(
    name="meta_ads_campaign_daily",
    columns=(
        *COMMON_COLUMNS,
        # Comme l'API Meta : dépense dans la devise du compte publicitaire.
        Column("spend", BigQueryType.FLOAT64, required=True),
        Column("account_currency", BigQueryType.STRING, required=True),
        Column("likes", BigQueryType.INT64),
        Column("comments", BigQueryType.INT64),
        Column("shares", BigQueryType.INT64),
        Column("video_views", BigQueryType.INT64),
        Column("page_engagement", BigQueryType.INT64),
        *AUDIT_COLUMNS,
    ),
)

TABLE_SPECS: Mapping[str, TableSpec] = MappingProxyType(
    {"google_ads": GOOGLE_ADS, "meta_ads": META_ADS},
)
"""Schéma de chaque source, par nom de source (lecture seule)."""
