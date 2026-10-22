"""Chargement réel dans BigQuery, dans un dataset jetable.

Lancement : ``ADSDATA_IT_PROJECT=<projet> uv run pytest -m integration``.
"""

import os
import uuid
from datetime import date

import pytest
from google.cloud import bigquery

from adsdata.config import Settings
from adsdata.ingestion.connectors.google_ads import GoogleAdsConnector
from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.loader import BigQueryLoader

pytestmark = pytest.mark.integration

PROJECT = os.environ.get("ADSDATA_IT_PROJECT")
LOCATION = "europe-west1"


@pytest.fixture(scope="module")
def loader():
    if not PROJECT:
        pytest.skip("ADSDATA_IT_PROJECT non défini")
    client = bigquery.Client(project=PROJECT, location=LOCATION)
    dataset = bigquery.Dataset(f"{PROJECT}.ads_it_{uuid.uuid4().hex[:8]}")
    dataset.location = LOCATION
    dataset.default_table_expiration_ms = 3_600_000
    client.create_dataset(dataset)
    try:
        yield BigQueryLoader(Settings(PROJECT, LOCATION, dataset.dataset_id), client)
    finally:
        client.delete_dataset(dataset, delete_contents=True, not_found_ok=True)


def count_rows(loader, spec):
    query = f"SELECT COUNT(*) AS n FROM `{loader.table_id(spec)}`"
    return next(iter(loader.client.query(query).result())).n


def test_replaying_a_window_gives_the_same_table(loader):
    connector = GoogleAdsConnector()
    month = DateWindow(date(2026, 9, 1), date(2026, 9, 30))
    expected = len(connector.extract(month))

    connector.run(month, loader, chunk_days=10)
    first = count_rows(loader, connector.spec)
    connector.run(month, loader, chunk_days=10)
    second = count_rows(loader, connector.spec)

    assert first == second == expected


def test_reloading_part_of_the_period_only_replaces_that_part(loader):
    connector = GoogleAdsConnector()
    week = DateWindow(date(2026, 9, 10), date(2026, 9, 16))
    before = count_rows(loader, connector.spec)

    connector.run(week, loader)

    assert count_rows(loader, connector.spec) == before
