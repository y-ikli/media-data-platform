"""Contrôles de qualité avant chargement : un lot invalide n'atteint jamais BigQuery."""

from __future__ import annotations

from datetime import date

from mdp.ingestion.schemas import TableSpec


class DataQualityError(ValueError):
    """Le lot extrait viole le contrat de la table raw."""


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise DataQualityError(f"Date invalide (AAAA-MM-JJ attendu) : {value!r}") from exc


def validate_rows(rows: list[dict], spec: TableSpec, start: date, end: date, max_errors: int = 10) -> None:
    """Vérifie colonnes, obligatoires, bornes de dates, positivité, unicité (date, campagne).

    Toutes les erreurs (jusqu'à ``max_errors``) sont rapportées ensemble pour faciliter le diagnostic.
    """
    errors: list[str] = []
    allowed = set(spec.column_names)
    seen: set[tuple[str, str]] = set()

    for i, row in enumerate(rows):
        unknown = set(row) - allowed
        if unknown:
            errors.append(f"ligne {i} : colonnes inconnues {sorted(unknown)}")
        for col in spec.required:
            if row.get(col) is None:
                errors.append(f"ligne {i} : {col} manquant")
        try:
            day = parse_date(row.get("date"))  # type: ignore[arg-type]
            if not start <= day <= end:
                errors.append(f"ligne {i} : date {day} hors de la fenêtre {start}..{end}")
        except DataQualityError as exc:
            errors.append(f"ligne {i} : {exc}")
        for col in spec.non_negative:
            value = row.get(col)
            if isinstance(value, (int, float)) and value < 0:
                errors.append(f"ligne {i} : {col} négatif ({value})")
        if isinstance(row.get("clicks"), int) and isinstance(row.get("impressions"), int) and row["clicks"] > row["impressions"]:
            errors.append(f"ligne {i} : clicks ({row['clicks']}) > impressions ({row['impressions']})")
        key = (str(row.get("date")), str(row.get("campaign_id")))
        if key in seen:
            errors.append(f"ligne {i} : doublon (date, campaign_id) = {key}")
        seen.add(key)
        if len(errors) >= max_errors:
            break

    if errors:
        raise DataQualityError("Lot rejeté :\n  - " + "\n  - ".join(errors[:max_errors]))
