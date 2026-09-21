"""Chargeur BigQuery : client simulé pour les appels, DuckDB pour la sémantique du remplacement de fenêtre."""

from datetime import date
from unittest.mock import MagicMock

import duckdb
import pytest

from mdp.config import ConfigError, Settings
from mdp.ingestion.loader import BigQueryLoader, replace_window_statements, schema_fields
from mdp.ingestion.schemas import META_ADS

SETTINGS = Settings(project_id="proj", location="EU", raw_dataset="raw")


def make_rows(days, campaigns=("a", "b"), value=1):
    return [{"date": f"2024-01-{d:02d}", "campaign_id": c, "v": value} for d in days for c in campaigns]


def test_schema_is_explicit_with_required_modes():
    fields = {f.name: f for f in schema_fields(META_ADS)}
    assert fields["date"].field_type == "DATE" and fields["date"].mode == "REQUIRED"
    assert fields["conversion_value"].field_type == "FLOAT64" and fields["conversion_value"].mode == "NULLABLE"
    assert fields["data_mode"].mode == "REQUIRED"


def test_loader_creates_a_partitioned_clustered_table_then_replaces_the_window():
    client = MagicMock()
    loader = BigQueryLoader(SETTINGS, client)
    n = loader.replace_window(META_ADS, [{"date": "2024-01-01"}], date(2024, 1, 1), date(2024, 1, 31), "ab-cd")

    assert n == 1
    table = client.create_table.call_args.args[0]
    assert table.time_partitioning.field == "date" and table.clustering_fields == ["campaign_id"]
    assert client.create_table.call_args.kwargs == {"exists_ok": True}

    load_args, load_kwargs = client.load_table_from_json.call_args
    assert load_args[1] == "proj.raw.meta_ads_campaign_daily__load_abcd"
    assert load_kwargs["job_config"].write_disposition == "WRITE_TRUNCATE" and load_kwargs["job_config"].schema

    script = client.query.call_args.args[0]
    assert "DELETE FROM `proj.raw.meta_ads_campaign_daily`" in script and "DATE '2024-01-31'" in script
    assert script.index("BEGIN TRANSACTION") < script.index("DELETE") < script.index("INSERT") < script.index("COMMIT")


def test_staging_table_is_dropped_even_when_the_script_fails():
    client = MagicMock()
    client.query.return_value.result.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        BigQueryLoader(SETTINGS, client).replace_window(
            META_ADS, [{"date": "2024-01-01"}], date(2024, 1, 1), date(2024, 1, 1), "r"
        )
    client.delete_table.assert_called_once_with("proj.raw.meta_ads_campaign_daily__load_r", not_found_ok=True)


def test_empty_batch_keeps_the_existing_window():
    client = MagicMock()
    assert BigQueryLoader(SETTINGS, client).replace_window(META_ADS, [], date(2024, 1, 1), date(2024, 1, 2), "r") == 0
    client.query.assert_not_called()


# --- sémantique du remplacement, exécutée pour de vrai (DuckDB accepte le même DELETE/INSERT) -----------------------


def run_replace(con, rows, start, end):
    con.execute("CREATE OR REPLACE TABLE staging (date DATE, campaign_id VARCHAR, v INTEGER)")
    con.executemany("INSERT INTO staging VALUES (?, ?, ?)", [(r["date"], r["campaign_id"], r["v"]) for r in rows])
    for stmt in replace_window_statements("target", "staging", start, end):
        con.execute(stmt.replace("`", '"'))


@pytest.fixture
def con():
    c = duckdb.connect()
    c.execute("CREATE TABLE target (date DATE, campaign_id VARCHAR, v INTEGER)")
    return c


def snapshot(con):
    return con.execute("SELECT date::VARCHAR, campaign_id, v FROM target ORDER BY 1, 2").fetchall()


def test_replaying_the_same_window_is_idempotent(con):
    rows = make_rows(range(1, 6))
    run_replace(con, rows, date(2024, 1, 1), date(2024, 1, 5))
    first = snapshot(con)
    run_replace(con, rows, date(2024, 1, 1), date(2024, 1, 5))
    run_replace(con, rows, date(2024, 1, 1), date(2024, 1, 5))
    assert snapshot(con) == first and len(first) == 10


def test_only_the_requested_window_is_replaced(con):
    run_replace(con, make_rows(range(1, 11)), date(2024, 1, 1), date(2024, 1, 10))
    run_replace(con, make_rows(range(4, 7), value=99), date(2024, 1, 4), date(2024, 1, 6))
    rows = snapshot(con)
    assert len(rows) == 20
    assert {r[2] for r in rows if "2024-01-04" <= r[0] <= "2024-01-06"} == {99}
    assert {r[2] for r in rows if r[0] < "2024-01-04" or r[0] > "2024-01-06"} == {1}


def test_a_campaign_that_left_the_source_disappears_from_the_window(con):
    run_replace(con, make_rows(range(1, 4)), date(2024, 1, 1), date(2024, 1, 3))
    run_replace(con, make_rows(range(1, 4), campaigns=("a",)), date(2024, 1, 1), date(2024, 1, 3))
    assert {r[1] for r in snapshot(con)} == {"a"}


def test_settings_require_a_project(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    with pytest.raises(ConfigError):
        Settings.from_env()
    monkeypatch.setenv("GCP_PROJECT_ID", "p")
    monkeypatch.setenv("BQ_RAW_DATASET", "custom")
    assert Settings.from_env() == Settings("p", "europe-west1", "custom")
