"""Zone raw locale (DuckDB) pour exécuter dbt sans BigQuery : tests, CI, développement hors ligne.

Les lignes sont produites par les vrais connecteurs simulés, enrichies et validées comme en production :
le test dbt exerce donc le même contrat de données que le pipeline réel.
"""

from __future__ import annotations

import argparse
import uuid
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from mdp.ingestion.base import DataSourceConnector
from mdp.ingestion.google_ads import GoogleAdsConnector
from mdp.ingestion.meta_ads import MetaAdsConnector
from mdp.ingestion.schemas import TableSpec
from mdp.ingestion.validation import parse_date, validate_rows

_DUCKDB_TYPES = {"DATE": "DATE", "STRING": "VARCHAR", "INT64": "BIGINT", "FLOAT64": "DOUBLE", "TIMESTAMP": "TIMESTAMPTZ"}


def _create(con: duckdb.DuckDBPyConnection, schema: str, spec: TableSpec) -> None:
    cols = ", ".join(f'"{n}" {_DUCKDB_TYPES[t]}{" NOT NULL" if req else ""}' for n, t, req in spec.columns)
    con.execute(f'CREATE OR REPLACE TABLE {schema}."{spec.name}" ({cols})')


def _insert(con: duckdb.DuckDBPyConnection, schema: str, spec: TableSpec, rows: list[dict]) -> None:
    names = spec.column_names
    placeholders = ", ".join("?" for _ in names)
    con.executemany(
        f'INSERT INTO {schema}."{spec.name}" ({", ".join(chr(34) + n + chr(34) for n in names)}) VALUES ({placeholders})',
        [tuple(r.get(n) for n in names) for r in rows],
    )


def _load(con, schema, connector: DataSourceConnector, start: str, end: str, ingested_at: datetime, scale: float = 1.0) -> int:
    rows = connector.enrich(connector.extract(start, end), str(uuid.uuid4()), ingested_at)
    if scale != 1.0:  # correction tardive simulée : la plateforme révise ses chiffres
        for r in rows:
            r["impressions"] = int(r["impressions"] * scale)
            r["clicks"] = min(r["clicks"], r["impressions"])
    validate_rows(rows, connector.spec, parse_date(start), parse_date(end))
    _insert(con, schema, connector.spec, rows)
    return len(rows)


def build(path: str | Path, start: str = "2024-01-01", end: str = "2024-03-31", with_reingestion: bool = True) -> dict:
    """Crée ``mdp_raw`` dans le fichier DuckDB ``path`` ; retourne le nombre de lignes par table.

    ``with_reingestion`` charge une seconde fois janvier avec des chiffres révisés (ancien mode append) :
    la couche staging doit ne garder que la dernière ingestion.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    con = duckdb.connect(str(path))
    con.execute("CREATE SCHEMA IF NOT EXISTS mdp_raw")
    first = datetime(2024, 4, 1, tzinfo=UTC)
    later = datetime(2024, 4, 8, tzinfo=UTC)
    counts: dict[str, int] = {}
    for connector in (GoogleAdsConnector(), MetaAdsConnector()):
        _create(con, "mdp_raw", connector.spec)
        n = _load(con, "mdp_raw", connector, start, end, first)
        if with_reingestion:
            n += _load(con, "mdp_raw", connector, start, "2024-01-31", later, scale=0.9)
        counts[connector.spec.name] = n
    con.close()
    return counts


def main() -> None:
    p = argparse.ArgumentParser(description="Construit la zone raw DuckDB pour dbt (cible `duckdb`).")
    p.add_argument("--path", default="dbt/mdp/target/ci.duckdb")
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--end", default="2024-03-31")
    p.add_argument("--no-reingestion", action="store_true")
    args = p.parse_args()
    print(build(args.path, args.start, args.end, not args.no_reingestion))


if __name__ == "__main__":
    main()
