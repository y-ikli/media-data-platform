"""Fixtures partagées par les tests."""

from collections.abc import Callable
from datetime import date

import pytest

from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.schemas import GOOGLE_ADS, META_ADS, TableSpec

type RowFactory = Callable[..., dict[str, object]]

_BASE_ROW: dict[str, object] = {
    "date": "2026-10-01",
    "campaign_id": "c1",
    "campaign_name": "Campagne 1",
    "impressions": 1000,
    "clicks": 50,
    "conversions": 2.5,
    "conversion_value": 120.0,
    "ingested_at": "2026-10-08T06:00:00+00:00",
    "extract_run_id": "run-1",
    "data_mode": "simulated",
}

_SOURCE_COLUMNS: dict[str, dict[str, object]] = {
    GOOGLE_ADS.name: {"source": "google_ads", "cost_micros": 12_340_000, "currency_code": "EUR"},
    META_ADS.name: {
        "source": "meta_ads",
        "spend": 12.34,
        "account_currency": "EUR",
        "likes": 3,
        "comments": 1,
        "shares": 0,
        "video_views": 40,
        "page_engagement": 7,
    },
}


@pytest.fixture
def window() -> DateWindow:
    return DateWindow(date(2026, 10, 1), date(2026, 10, 7))


@pytest.fixture
def make_row() -> RowFactory:
    """Fabrique une ligne valide pour ``spec`` ; les arguments nommés remplacent des valeurs."""

    def factory(spec: TableSpec = GOOGLE_ADS, **overrides: object) -> dict[str, object]:
        return {**_BASE_ROW, **_SOURCE_COLUMNS[spec.name], **overrides}

    return factory
