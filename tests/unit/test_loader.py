from datetime import date
from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from adsdata.config import ConfigError, Settings
from adsdata.ingestion import loader as loader_module
from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.loader import (
    BigQueryLoader,
    SchemaMismatchError,
    replace_window_script,
    schema_fields,
)
from adsdata.ingestion.schemas import GOOGLE_ADS

SETTINGS = Settings(project_id="proj", location="europe-west1", raw_dataset="raw")
TARGET = "proj.raw.google_ads_campaign_daily"
WEEK = DateWindow(date(2026, 10, 1), date(2026, 10, 7))


def legacy_named(fields):
    """Schéma tel que BigQuery le renvoie : anciens noms de types."""
    names = {"INT64": "INTEGER", "FLOAT64": "FLOAT"}
    return [
        bigquery.SchemaField(f.name, names.get(f.field_type, f.field_type), f.mode) for f in fields
    ]


@pytest.fixture
def client():
    fake = MagicMock(spec=bigquery.Client)
    fake.get_table.return_value = MagicMock(schema=legacy_named(schema_fields(GOOGLE_ADS)))
    return fake


def test_schema_follows_the_declaration():
    fields = {f.name: f for f in schema_fields(GOOGLE_ADS)}

    assert list(fields) == list(GOOGLE_ADS.column_names)
    assert (fields["cost_micros"].field_type, fields["cost_micros"].mode) == ("INT64", "REQUIRED")
    assert fields["campaign_name"].mode == "NULLABLE"


def test_script_replaces_the_window_inside_a_transaction():
    script = replace_window_script(GOOGLE_ADS, TARGET, "staging")

    lines = script.splitlines()
    assert lines[0] == "BEGIN TRANSACTION;"
    assert lines[1] == f"DELETE FROM `{TARGET}` WHERE `date` BETWEEN @start AND @end;"
    assert lines[2].startswith(f"INSERT INTO `{TARGET}` (`date`, `campaign_id`,")
    assert lines[2].endswith("FROM `staging`;")
    assert lines[3] == "COMMIT TRANSACTION;"


def test_missing_dataset_points_to_terraform(client):
    client.get_dataset.side_effect = NotFound("absent")

    with pytest.raises(ConfigError, match="Terraform"):
        BigQueryLoader(SETTINGS, client).ensure_table(GOOGLE_ADS)
    client.create_dataset.assert_not_called()


def test_missing_table_is_created_partitioned_and_clustered(client):
    client.get_table.side_effect = NotFound("absente")

    BigQueryLoader(SETTINGS, client).ensure_table(GOOGLE_ADS)

    table = client.create_table.call_args.args[0]
    assert table.table_id == "google_ads_campaign_daily"
    assert table.time_partitioning.field == "date"
    assert table.clustering_fields == ["campaign_id"]


def test_existing_table_with_the_same_schema_is_kept(client):
    BigQueryLoader(SETTINGS, client).ensure_table(GOOGLE_ADS)

    client.create_table.assert_not_called()


def test_existing_table_with_another_schema_is_refused(client):
    client.get_table.return_value = MagicMock(schema=schema_fields(GOOGLE_ADS)[:-1])

    with pytest.raises(SchemaMismatchError, match="schéma différent"):
        BigQueryLoader(SETTINGS, client).ensure_table(GOOGLE_ADS)


def test_empty_batch_deletes_nothing(client):
    assert BigQueryLoader(SETTINGS, client).replace_window(GOOGLE_ADS, [], WEEK, "r") == 0

    client.query.assert_not_called()
    client.load_table_from_json.assert_not_called()


def test_replace_window_loads_then_swaps_then_cleans_up(client):
    rows = [{"date": "2026-10-01", "campaign_id": "c1"}]

    loaded = BigQueryLoader(SETTINGS, client).replace_window(GOOGLE_ADS, rows, WEEK, "ab-cd")

    staging_id = f"{TARGET}__load_abcd"
    staging = client.create_table.call_args.args[0]
    assert staging.table_id == "google_ads_campaign_daily__load_abcd"
    assert staging.expires is not None
    assert client.load_table_from_json.call_args.args == (rows, staging_id)
    query, kwargs = client.query.call_args.args[0], client.query.call_args.kwargs
    assert query == replace_window_script(GOOGLE_ADS, TARGET, staging_id)
    params = {p.name: p.value for p in kwargs["job_config"].query_parameters}
    assert params == {"start": WEEK.start, "end": WEEK.end}
    client.delete_table.assert_called_once_with(staging_id, not_found_ok=True)
    assert loaded == 1


def test_staging_table_is_removed_even_when_the_swap_fails(client):
    client.query.return_value.result.side_effect = RuntimeError("transaction annulée")

    with pytest.raises(RuntimeError, match="annulée"):
        BigQueryLoader(SETTINGS, client).replace_window(GOOGLE_ADS, [{"x": 1}], WEEK, "r")

    client.delete_table.assert_called_once()


def test_client_is_created_lazily_for_the_configured_project(monkeypatch):
    created = MagicMock()
    monkeypatch.setattr(loader_module.bigquery, "Client", created)
    loader = BigQueryLoader(SETTINGS)

    created.assert_not_called()
    assert loader.client is created.return_value
    assert loader.client is created.return_value
    created.assert_called_once_with(project="proj", location="europe-west1")
