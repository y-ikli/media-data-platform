"""Contrat de données : contrôles appliqués à un lot avant tout chargement.

Un lot invalide n'atteint jamais BigQuery. Toutes les erreurs sont rapportées ensemble (dans la
limite de ``max_errors``) pour pouvoir tout corriger d'un coup.

Chaque règle est une fonction ``(row, spec, window) -> erreurs`` ; ajouter une règle revient à
l'écrire et à l'ajouter à ``ROW_RULES``.
"""

import math
from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import datetime
from typing import assert_never

from adsdata.ingestion.dates import DateWindow, parse_date
from adsdata.ingestion.schemas import BigQueryType, TableSpec

type Row = Mapping[str, object]
type RowRule = Callable[[Row, TableSpec, DateWindow], Iterator[str]]

DEFAULT_MAX_ERRORS = 10


class DataQualityError(ValueError):
    """Le lot viole le contrat de la table ; ``errors`` liste les problèmes trouvés."""

    def __init__(self, errors: Sequence[str]) -> None:
        """Garde la liste des erreurs et construit un message lisible."""
        self.errors = tuple(errors)
        super().__init__("Lot rejeté :\n  - " + "\n  - ".join(self.errors))


def _is_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parse_date(value)
    except ValueError:
        return False
    return True


def _is_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _as_number(value: object) -> int | float | None:
    """Renvoie ``value`` si c'est un nombre (un booléen n'en est pas un), sinon ``None``."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return value


def matches_type(value: object, bq_type: BigQueryType) -> bool:
    """Indique si ``value`` est acceptable pour une colonne ``bq_type`` dans un chargement JSON.

    Les dates et horodatages sont attendus en texte ISO 8601. Un booléen n'est jamais un nombre,
    et un nombre à virgule doit être fini.
    """
    if isinstance(value, bool):
        return False
    match bq_type:
        case BigQueryType.INT64:
            return isinstance(value, int)
        case BigQueryType.FLOAT64:
            return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))
        case BigQueryType.STRING:
            return isinstance(value, str)
        case BigQueryType.DATE:
            return _is_date(value)
        case BigQueryType.TIMESTAMP:
            return _is_timestamp(value)
        case _ as unreachable:  # pragma: no cover
            assert_never(unreachable)


def check_unknown_columns(row: Row, spec: TableSpec, window: DateWindow) -> Iterator[str]:
    """Signale les colonnes absentes du schéma."""
    unknown = sorted(set(row) - set(spec.column_names))
    if unknown:
        yield f"colonnes inconnues {unknown}"


def check_required(row: Row, spec: TableSpec, window: DateWindow) -> Iterator[str]:
    """Signale les colonnes obligatoires absentes ou nulles."""
    for column in spec.columns:
        if column.required and row.get(column.name) is None:
            yield f"{column.name} manquant"


def check_types(row: Row, spec: TableSpec, window: DateWindow) -> Iterator[str]:
    """Signale les valeurs dont le type ne correspond pas au schéma."""
    for column in spec.columns:
        value = row.get(column.name)
        if value is not None and not matches_type(value, column.bq_type):
            yield f"{column.name} : {value!r} n'est pas un {column.bq_type}"


def check_allowed_values(row: Row, spec: TableSpec, window: DateWindow) -> Iterator[str]:
    """Signale les valeurs hors de la liste autorisée par le schéma."""
    for column in spec.columns:
        value = row.get(column.name)
        allowed = column.allowed_values
        if allowed is not None and value is not None and value not in allowed:
            yield f"{column.name} : {value!r} hors de {sorted(allowed)}"


def check_partition_in_window(row: Row, spec: TableSpec, window: DateWindow) -> Iterator[str]:
    """Signale une date de partition en dehors de la fenêtre demandée."""
    value = row.get(spec.partition_field)
    if isinstance(value, str) and _is_date(value):
        day = parse_date(value)
        if day not in window:
            yield f"{spec.partition_field} {day} hors de la fenêtre {window}"


def check_non_negative(row: Row, spec: TableSpec, window: DateWindow) -> Iterator[str]:
    """Signale les nombres négatifs : aucune métrique publicitaire ne peut l'être."""
    for column in spec.columns:
        value = _as_number(row.get(column.name))
        if column.is_numeric and value is not None and value < 0:
            yield f"{column.name} négatif ({value})"


def check_clicks_vs_impressions(row: Row, spec: TableSpec, window: DateWindow) -> Iterator[str]:
    """Signale plus de clics que d'impressions (impossible : un clic suit un affichage)."""
    clicks, impressions = _as_number(row.get("clicks")), _as_number(row.get("impressions"))
    if clicks is not None and impressions is not None and clicks > impressions:
        yield f"clicks ({clicks}) > impressions ({impressions})"


ROW_RULES: tuple[RowRule, ...] = (
    check_unknown_columns,
    check_required,
    check_types,
    check_allowed_values,
    check_partition_in_window,
    check_non_negative,
    check_clicks_vs_impressions,
)
"""Règles appliquées à chaque ligne, dans cet ordre."""


def _iter_errors(rows: Sequence[Row], spec: TableSpec, window: DateWindow) -> Iterator[str]:
    seen: set[tuple[object, ...]] = set()
    for index, row in enumerate(rows):
        for rule in ROW_RULES:
            for message in rule(row, spec, window):
                yield f"ligne {index} : {message}"
        key = tuple(row.get(name) for name in spec.unique_key)
        if key in seen:
            yield f"ligne {index} : doublon sur {spec.unique_key} = {key}"
        seen.add(key)


def validate_rows(
    rows: Sequence[Row],
    spec: TableSpec,
    window: DateWindow,
    max_errors: int = DEFAULT_MAX_ERRORS,
) -> None:
    """Vérifie un lot entier ; lève ``DataQualityError`` au moindre problème.

    Un lot vide est valide : c'est le chargeur qui décide quoi faire d'une extraction vide.
    """
    if max_errors < 1:
        raise ValueError("max_errors doit être ≥ 1")
    errors: list[str] = []
    for message in _iter_errors(rows, spec, window):
        if len(errors) == max_errors:
            errors.append(f"… arrêt après {max_errors} erreurs")
            break
        errors.append(message)
    if errors:
        raise DataQualityError(errors)
