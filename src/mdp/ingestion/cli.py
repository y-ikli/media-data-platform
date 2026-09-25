"""Point d'entrée : ``mdp-ingest --source meta_ads --start 2024-01-01 --end 2024-03-31``."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

from mdp.config import ConfigError, Settings
from mdp.ingestion.base import DEFAULT_CHUNK_DAYS, DataSourceConnector
from mdp.ingestion.google_ads import GoogleAdsConnector
from mdp.ingestion.loader import BigQueryLoader
from mdp.ingestion.meta_ads import MetaAdsConnector
from mdp.ingestion.validation import DataQualityError

CONNECTORS: dict[str, type[DataSourceConnector]] = {"meta_ads": MetaAdsConnector, "google_ads": GoogleAdsConnector}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mdp-ingest", description="Ingère une source publicitaire dans BigQuery (idempotent).")
    p.add_argument("--source", required=True, choices=sorted(CONNECTORS))
    p.add_argument("--start", help="AAAA-MM-JJ")
    p.add_argument("--end", help="AAAA-MM-JJ (inclus)")
    p.add_argument(
        "--lookback-days",
        type=int,
        metavar="N",
        help="fenêtre glissante [J-N, J-1] (exécution planifiée) ; exclusif avec --start/--end",
    )
    p.add_argument(
        "--mode",
        choices=["simulated", "real"],
        default="simulated",
        help="simulated (défaut) : données générées ; real : API de la plateforme",
    )
    p.add_argument("--chunk-days", type=int, default=DEFAULT_CHUNK_DAYS)
    p.add_argument("--dry-run", action="store_true", help="extrait et valide sans écrire dans BigQuery")
    return p


def resolve_window(args: argparse.Namespace, today: date | None = None) -> tuple[str, str]:
    """Fenêtre à ingérer : bornes explicites, ou les N derniers jours complets (jusqu'à hier inclus)."""
    if args.lookback_days is not None:
        if args.start or args.end:
            raise ValueError("--lookback-days est exclusif avec --start/--end")
        if args.lookback_days < 1:
            raise ValueError("--lookback-days doit être ≥ 1")
        yesterday = (today or date.today()) - timedelta(days=1)
        return (yesterday - timedelta(days=args.lookback_days - 1)).isoformat(), yesterday.isoformat()
    if not (args.start and args.end):
        raise ValueError("--start et --end sont requis (ou --lookback-days)")
    return args.start, args.end


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = build_parser().parse_args(argv)
    try:
        start, end = resolve_window(args)
        connector = CONNECTORS[args.source](args.mode)
        loader = None if args.dry_run else BigQueryLoader(Settings.from_env())
        reports = connector.run(start, end, loader, args.chunk_days, args.dry_run)
    except (ConfigError, NotImplementedError, DataQualityError, ValueError) as exc:
        logging.getLogger("mdp").error("%s", exc)
        return 2
    total = sum(r.rows for r in reports)
    logging.getLogger("mdp").info(
        "Terminé : %d lignes, %d fenêtre(s)%s", total, len(reports), " (dry-run)" if args.dry_run else ""
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
