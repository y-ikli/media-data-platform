"""Contrat commun des connecteurs de sources publicitaires.

Une sous-classe n'implémente que ``extract()`` ; l'enrichissement (métadonnées d'audit), la validation,
le découpage en fenêtres et le chargement idempotent sont fournis ici et identiques pour toutes les sources.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta

from mdp.ingestion.loader import BigQueryLoader
from mdp.ingestion.schemas import DATA_MODES, TableSpec
from mdp.ingestion.validation import parse_date, validate_rows

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_DAYS = 92  # les API publicitaires expirent sur de longues plages


@dataclass
class IngestionReport:
    """Trace d'une exécution : journalisée en JSON, une ligne par fenêtre."""

    source: str
    data_mode: str
    table: str
    start: str
    end: str
    rows: int
    extract_run_id: str
    duration_s: float
    dry_run: bool


def date_windows(start: date, end: date, chunk_days: int) -> list[tuple[date, date]]:
    """Découpe ``[start, end]`` en fenêtres contiguës d'au plus ``chunk_days`` jours."""
    if end < start:
        raise ValueError(f"Fenêtre inversée : {start} > {end}")
    if chunk_days < 1:
        raise ValueError("chunk_days doit être ≥ 1")
    windows, cursor = [], start
    while cursor <= end:
        last = min(cursor + timedelta(days=chunk_days - 1), end)
        windows.append((cursor, last))
        cursor = last + timedelta(days=1)
    return windows


class DataSourceConnector(ABC):
    """Base des connecteurs. ``data_mode`` : ``real`` (API) ou ``simulated`` (données générées)."""

    spec: TableSpec
    source_name: str

    def __init__(self, data_mode: str = "simulated"):
        if data_mode not in DATA_MODES:
            raise ValueError(f"data_mode doit être l'un de {DATA_MODES}, reçu {data_mode!r}")
        self.data_mode = data_mode

    @abstractmethod
    def extract(self, start_date: str, end_date: str) -> list[dict]:
        """Extrait les lignes brutes de ``[start_date, end_date]`` (bornes incluses, AAAA-MM-JJ)."""

    def enrich(self, rows: list[dict], run_id: str, ingested_at: datetime | None = None) -> list[dict]:
        """Ajoute les métadonnées d'audit communes à toutes les sources."""
        stamp = (ingested_at or datetime.now(tz=UTC)).isoformat()
        return [
            {**row, "ingested_at": stamp, "extract_run_id": run_id, "source": self.source_name, "data_mode": self.data_mode}
            for row in rows
        ]

    def run(
        self,
        start_date: str,
        end_date: str,
        loader: BigQueryLoader | None = None,
        chunk_days: int = DEFAULT_CHUNK_DAYS,
        dry_run: bool = False,
    ) -> list[IngestionReport]:
        """Extrait, valide et charge ``[start_date, end_date]`` fenêtre par fenêtre (idempotent)."""
        start, end = parse_date(start_date), parse_date(end_date)
        if not dry_run and loader is None:
            raise ValueError("Un loader est requis hors dry-run")

        reports = []
        for win_start, win_end in date_windows(start, end, chunk_days):
            t0 = time.monotonic()
            run_id = str(uuid.uuid4())
            raw = self.extract(win_start.isoformat(), win_end.isoformat())
            rows = self.enrich(raw, run_id)
            validate_rows(rows, self.spec, win_start, win_end)
            if not dry_run and loader is not None:
                loader.replace_window(self.spec, rows, win_start, win_end, run_id)
            report = IngestionReport(
                source=self.source_name,
                data_mode=self.data_mode,
                table=self.spec.name,
                start=win_start.isoformat(),
                end=win_end.isoformat(),
                rows=len(rows),
                extract_run_id=run_id,
                duration_s=round(time.monotonic() - t0, 2),
                dry_run=dry_run,
            )
            logger.info("ingestion %s", json.dumps(asdict(report)))
            reports.append(report)
        return reports
