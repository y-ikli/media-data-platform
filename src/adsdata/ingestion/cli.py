"""Commande ``adsdata-ingest`` : ingère une source publicitaire dans BigQuery.

Exemples ::

    adsdata-ingest --source google_ads --start 2026-01-01 --end 2026-03-31
    adsdata-ingest --source meta_ads --mode real --lookback-days 7
    adsdata-ingest --source google_ads --lookback-days 7 --dry-run
"""

import argparse
import logging
import sys
from collections.abc import Sequence
from datetime import date

from dotenv import load_dotenv

from adsdata.config import ConfigError, Settings
from adsdata.ingestion.base import DEFAULT_CHUNK_DAYS
from adsdata.ingestion.connectors import CONNECTORS
from adsdata.ingestion.dates import DateWindow, parse_date
from adsdata.ingestion.loader import BigQueryLoader, SchemaMismatchError
from adsdata.ingestion.schemas import DataMode
from adsdata.ingestion.validation import DataQualityError

logger = logging.getLogger("adsdata")

EXIT_OK = 0
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    """Arguments de la commande."""
    parser = argparse.ArgumentParser(
        prog="adsdata-ingest",
        description="Ingère une source publicitaire dans BigQuery (chargement idempotent).",
    )
    parser.add_argument("--source", required=True, choices=sorted(CONNECTORS))
    parser.add_argument("--start", help="premier jour, AAAA-MM-JJ")
    parser.add_argument("--end", help="dernier jour inclus, AAAA-MM-JJ")
    parser.add_argument(
        "--lookback-days",
        type=int,
        metavar="N",
        help="les N derniers jours complets, jusqu'à hier (exclusif avec --start/--end)",
    )
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in DataMode],
        default=DataMode.SIMULATED.value,
        help="simulated (défaut) : données générées ; real : API de la plateforme",
    )
    parser.add_argument("--chunk-days", type=int, default=DEFAULT_CHUNK_DAYS)
    parser.add_argument(
        "--dry-run", action="store_true", help="extrait et valide sans rien écrire"
    )
    return parser


def resolve_window(args: argparse.Namespace, today: date) -> DateWindow:
    """Période à ingérer : bornes explicites, ou les N derniers jours complets."""
    if args.lookback_days is not None:
        if args.start or args.end:
            raise ValueError("--lookback-days est exclusif avec --start/--end")
        return DateWindow.last_days(args.lookback_days, today)
    if not (args.start and args.end):
        raise ValueError("--start et --end sont requis (ou --lookback-days)")
    return DateWindow(parse_date(args.start), parse_date(args.end))


def main(argv: Sequence[str] | None = None, today: date | None = None) -> int:
    """Point d'entrée ; renvoie le code de sortie (0 si tout s'est bien passé)."""
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    args = build_parser().parse_args(argv)
    try:
        window = resolve_window(args, today or date.today())
        connector = CONNECTORS[args.source](DataMode(args.mode))
        loader = None if args.dry_run else BigQueryLoader(Settings.from_env())
        reports = connector.run(window, loader, chunk_days=args.chunk_days, dry_run=args.dry_run)
    except (
        ConfigError,
        DataQualityError,
        NotImplementedError,
        SchemaMismatchError,
        ValueError,
    ) as exc:
        logger.error("%s", exc)
        return EXIT_ERROR
    total = sum(report.extracted_rows for report in reports)
    suffix = " (dry-run, rien n'a été écrit)" if args.dry_run else ""
    logger.info("terminé : %d lignes, %d fenêtre(s)%s", total, len(reports), suffix)
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
