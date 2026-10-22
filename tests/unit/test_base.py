import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from itertools import count

import pytest

from adsdata.ingestion.base import Connector, IngestionReport
from adsdata.ingestion.dates import DateWindow
from adsdata.ingestion.schemas import GOOGLE_ADS, DataMode
from adsdata.ingestion.validation import DataQualityError

FIXED_NOW = datetime(2026, 10, 17, 6, 0, tzinfo=UTC)


@dataclass
class FakeLoader:
    calls: list[tuple[str, int, DateWindow, str]] = field(default_factory=list)

    def replace_window(self, spec, rows, window, run_id):
        self.calls.append((spec.name, len(rows), window, run_id))
        return len(rows)


class OneRowPerDay(Connector):
    source_name = "fake"
    spec = GOOGLE_ADS

    def __init__(self, broken_day: date | None = None, **kwargs):
        ids = count(1)
        super().__init__(
            DataMode.SIMULATED,
            clock=lambda: FIXED_NOW,
            run_id_factory=lambda: f"run-{next(ids)}",
            **kwargs,
        )
        self.broken_day = broken_day

    def extract(self, window):
        return [
            {
                "date": day.isoformat(),
                "campaign_id": "c1",
                "impressions": 100,
                "clicks": 500 if day == self.broken_day else 5,
                "cost_micros": 1_000_000,
                "currency_code": "EUR",
            }
            for day in window.days()
        ]


TEN_DAYS = DateWindow(date(2026, 10, 1), date(2026, 10, 10))


def test_run_loads_each_chunk_with_its_own_run_id():
    loader = FakeLoader()

    reports = OneRowPerDay().run(TEN_DAYS, loader, chunk_days=4)

    assert [(c[1], str(c[2]), c[3]) for c in loader.calls] == [
        (4, "2026-10-01..2026-10-04", "run-1"),
        (4, "2026-10-05..2026-10-08", "run-2"),
        (2, "2026-10-09..2026-10-10", "run-3"),
    ]
    assert [r.loaded_rows for r in reports] == [4, 4, 2]
    assert all(not r.dry_run for r in reports)


def test_enrich_adds_audit_columns():
    connector = OneRowPerDay()

    (row,) = connector.enrich([{"campaign_id": "c1", "source": "écrasée"}], "run-x")

    assert row == {
        "campaign_id": "c1",
        "ingested_at": "2026-10-17T06:00:00+00:00",
        "extract_run_id": "run-x",
        "source": "fake",
        "data_mode": "simulated",
    }


def test_dry_run_never_calls_the_loader():
    loader = FakeLoader()

    reports = OneRowPerDay().run(TEN_DAYS, loader, dry_run=True)

    assert loader.calls == []
    assert reports[0].extracted_rows == 10
    assert reports[0].loaded_rows == 0
    assert reports[0].dry_run


def test_a_loader_is_required_outside_dry_run():
    with pytest.raises(ValueError, match="chargeur"):
        OneRowPerDay().run(TEN_DAYS)


def test_invalid_chunk_is_never_loaded_but_previous_chunks_are():
    loader = FakeLoader()

    with pytest.raises(DataQualityError, match="clicks"):
        OneRowPerDay(broken_day=date(2026, 10, 6)).run(TEN_DAYS, loader, chunk_days=4)

    assert [str(c[2]) for c in loader.calls] == ["2026-10-01..2026-10-04"]


def test_each_chunk_is_logged_as_json(caplog):
    with caplog.at_level(logging.INFO, logger="adsdata.ingestion.base"):
        OneRowPerDay().run(TEN_DAYS, dry_run=True)

    payload = json.loads(caplog.records[0].getMessage().removeprefix("ingestion "))
    assert payload["source"] == "fake"
    assert payload["extracted_rows"] == 10


def test_report_serialises_to_one_json_line():
    report = IngestionReport(
        "s", "simulated", "t", "2026-10-01", "2026-10-02", 2, 2, "r", 0.1, False
    )

    assert json.loads(report.to_json())["table"] == "t"
    assert "\n" not in report.to_json()


def test_unknown_data_mode_is_rejected():
    with pytest.raises(ValueError, match="faux"):
        OneRowPerDay.__base__.__init__(object.__new__(OneRowPerDay), "faux")
