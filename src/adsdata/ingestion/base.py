"""Socle commun des connecteurs : fenêtres, enrichissement, validation, chargement, journal.

Un connecteur ne fournit que son nom, son schéma et ``extract()``. Tout le reste est ici,
identique pour toutes les sources.
"""

import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import ClassVar, Protocol

from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.schemas import DataMode, TableSpec
from adsdata.ingestion.validation import Row, validate_rows

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_DAYS = 92
"""Taille maximale d'une fenêtre : les API publicitaires supportent mal les longues périodes."""


class Loader(Protocol):
    """Ce que l'ingestion attend d'un chargeur : BigQuery en production, un faux en test."""

    def replace_window(
        self, spec: TableSpec, rows: Sequence[Row], window: DateWindow, run_id: str
    ) -> int:
        """Remplace les lignes de ``window`` par ``rows`` ; renvoie le nombre chargé."""
        ...


@dataclass(frozen=True, slots=True)
class IngestionReport:
    """Trace d'une fenêtre ingérée, journalisée en JSON."""

    source: str
    data_mode: str
    table: str
    start: str
    end: str
    extracted_rows: int
    loaded_rows: int
    extract_run_id: str
    duration_s: float
    dry_run: bool

    def to_json(self) -> str:
        """Sérialise le rapport sur une ligne JSON."""
        return json.dumps(asdict(self), ensure_ascii=False)


def utc_now() -> datetime:
    """Heure courante en UTC."""
    return datetime.now(tz=UTC)


def new_run_id() -> str:
    """Identifiant unique d'une exécution."""
    return str(uuid.uuid4())


class Connector(ABC):
    """Base de tous les connecteurs de sources publicitaires."""

    source_name: ClassVar[str]
    spec: ClassVar[TableSpec]

    def __init__(
        self,
        data_mode: DataMode = DataMode.SIMULATED,
        *,
        clock: Callable[[], datetime] = utc_now,
        run_id_factory: Callable[[], str] = new_run_id,
    ) -> None:
        """Prépare le connecteur ; ``clock`` et ``run_id_factory`` se remplacent en test."""
        self.data_mode = DataMode(data_mode)
        self._clock = clock
        self._new_run_id = run_id_factory

    @abstractmethod
    def extract(self, window: DateWindow) -> list[dict[str, object]]:
        """Lignes brutes de la source pour chaque jour de ``window``, au format de la table raw."""

    def enrich(self, rows: Sequence[Row], run_id: str) -> list[dict[str, object]]:
        """Ajoute les colonnes d'audit à chaque ligne (elles écrasent d'éventuelles homonymes)."""
        audit: dict[str, object] = {
            "ingested_at": self._clock().isoformat(),
            "extract_run_id": run_id,
            "source": self.source_name,
            "data_mode": self.data_mode.value,
        }
        return [{**row, **audit} for row in rows]

    def run(
        self,
        window: DateWindow,
        loader: Loader | None = None,
        *,
        chunk_days: int = DEFAULT_CHUNK_DAYS,
        dry_run: bool = False,
    ) -> list[IngestionReport]:
        """Extrait, valide et charge ``window``, fenêtre par fenêtre.

        Chaque fenêtre est validée entièrement avant d'être chargée : un lot invalide lève
        ``DataQualityError`` et rien n'est écrit pour cette fenêtre. En ``dry_run``, rien n'est
        jamais écrit.
        """
        if loader is None and not dry_run:
            raise ValueError("un chargeur est requis hors dry-run")

        reports: list[IngestionReport] = []
        for chunk in window.split(chunk_days):
            started = time.monotonic()
            run_id = self._new_run_id()
            rows = self.enrich(self.extract(chunk), run_id)
            validate_rows(rows, self.spec, chunk)
            loaded = 0
            if loader is not None and not dry_run:
                loaded = loader.replace_window(self.spec, rows, chunk, run_id)
            report = IngestionReport(
                source=self.source_name,
                data_mode=self.data_mode.value,
                table=self.spec.name,
                start=chunk.start.isoformat(),
                end=chunk.end.isoformat(),
                extracted_rows=len(rows),
                loaded_rows=loaded,
                extract_run_id=run_id,
                duration_s=round(time.monotonic() - started, 3),
                dry_run=dry_run,
            )
            logger.info("ingestion %s", report.to_json())
            reports.append(report)
        return reports
