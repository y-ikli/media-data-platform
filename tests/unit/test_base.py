from datetime import date

import pytest

from mdp.ingestion.base import date_windows
from mdp.ingestion.google_ads import GoogleAdsConnector
from mdp.ingestion.meta_ads import MetaAdsConnector
from mdp.ingestion.validation import DataQualityError


class RecordingLoader:
    def __init__(self):
        self.calls = []

    def replace_window(self, spec, rows, start, end, run_id):
        self.calls.append((spec.name, len(rows), start, end, run_id))
        return len(rows)


def test_windows_cover_the_range_without_gap_or_overlap():
    w = date_windows(date(2024, 1, 1), date(2024, 12, 31), 92)
    assert w[0][0] == date(2024, 1, 1) and w[-1][1] == date(2024, 12, 31)
    assert all((b[0] - a[1]).days == 1 for a, b in zip(w, w[1:], strict=False))
    assert all((e - s).days + 1 <= 92 for s, e in w)


@pytest.mark.parametrize("start,end,chunk", [(date(2024, 2, 1), date(2024, 1, 1), 10), (date(2024, 1, 1), date(2024, 1, 2), 0)])
def test_invalid_windows(start, end, chunk):
    with pytest.raises(ValueError):
        date_windows(start, end, chunk)


def test_enrichment_adds_audit_metadata():
    rows = MetaAdsConnector().enrich([{"date": "2024-01-01"}], "run-1")
    assert rows[0]["extract_run_id"] == "run-1" and rows[0]["source"] == "meta_ads"
    assert rows[0]["data_mode"] == "simulated" and rows[0]["ingested_at"].endswith("+00:00")


def test_run_loads_one_window_per_chunk():
    loader = RecordingLoader()
    reports = GoogleAdsConnector().run("2024-01-01", "2024-03-31", loader, chunk_days=31)
    assert [(c[2], c[3]) for c in loader.calls] == [
        (date(2024, 1, 1), date(2024, 1, 31)),
        (date(2024, 2, 1), date(2024, 3, 2)),
        (date(2024, 3, 3), date(2024, 3, 31)),
    ]
    assert sum(r.rows for r in reports) == 91 * 5 and all(not r.dry_run for r in reports)


def test_dry_run_never_touches_the_loader():
    reports = MetaAdsConnector().run("2024-01-01", "2024-01-05", loader=None, dry_run=True)
    assert reports[0].rows == 5 * 4 and reports[0].dry_run


def test_loader_is_required_outside_dry_run():
    with pytest.raises(ValueError, match="loader"):
        MetaAdsConnector().run("2024-01-01", "2024-01-05")


def test_invalid_batch_is_rejected_before_loading():
    class Broken(GoogleAdsConnector):
        def extract(self, start_date, end_date):
            rows = super().extract(start_date, end_date)
            rows[0]["clicks"] = rows[0]["impressions"] + 1
            return rows

    loader = RecordingLoader()
    with pytest.raises(DataQualityError):
        Broken().run("2024-01-01", "2024-01-02", loader)
    assert loader.calls == []


def test_real_mode_never_falls_back_silently():
    with pytest.raises(NotImplementedError):
        GoogleAdsConnector("real")
    with pytest.raises(Exception, match="extra `meta`|manquantes"):
        MetaAdsConnector("real")


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        MetaAdsConnector("fake")
