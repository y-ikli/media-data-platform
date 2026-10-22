import argparse
from datetime import date

import pytest

from adsdata.ingestion import cli
from adsdata.ingestion.dates import DateWindow

TODAY = date(2026, 10, 17)


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    """Ne pas lire le vrai .env du projet pendant les tests."""
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)


def args(**kwargs):
    return argparse.Namespace(**{"start": None, "end": None, "lookback_days": None, **kwargs})


def test_explicit_bounds():
    window = cli.resolve_window(args(start="2026-01-01", end="2026-01-31"), TODAY)

    assert window == DateWindow(date(2026, 1, 1), date(2026, 1, 31))


def test_lookback_days_ends_yesterday():
    assert str(cli.resolve_window(args(lookback_days=3), TODAY)) == "2026-10-14..2026-10-16"


@pytest.mark.parametrize(
    ("namespace", "message"),
    [
        (args(lookback_days=3, start="2026-01-01"), "exclusif"),
        (args(start="2026-01-01"), "requis"),
        (args(), "requis"),
    ],
)
def test_invalid_period_arguments(namespace, message):
    with pytest.raises(ValueError, match=message):
        cli.resolve_window(namespace, TODAY)


def test_dry_run_succeeds_without_any_configuration(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)

    code = cli.main(["--source", "google_ads", "--lookback-days", "3", "--dry-run"], today=TODAY)

    assert code == cli.EXIT_OK


def test_load_uses_the_bigquery_loader(monkeypatch):
    created = []

    class FakeLoader:
        def __init__(self, settings):
            created.append(settings)

        def replace_window(self, spec, rows, window, run_id):
            return len(rows)

    monkeypatch.setenv("GCP_PROJECT_ID", "proj")
    monkeypatch.setattr(cli, "BigQueryLoader", FakeLoader)

    code = cli.main(["--source", "meta_ads", "--start", "2026-10-01", "--end", "2026-10-02"])

    assert code == cli.EXIT_OK
    assert created[0].project_id == "proj"


@pytest.mark.parametrize(
    "argv",
    [
        ["--source", "google_ads", "--mode", "real", "--lookback-days", "3"],
        ["--source", "google_ads", "--start", "2026-10-02", "--end", "2026-10-01", "--dry-run"],
        ["--source", "google_ads", "--lookback-days", "3"],
    ],
    ids=["mode-reel-indisponible", "fenetre-inversee", "projet-manquant"],
)
def test_errors_return_a_non_zero_code(argv, monkeypatch, caplog):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)

    assert cli.main(argv, today=TODAY) == cli.EXIT_ERROR
    assert caplog.records[-1].levelname == "ERROR"
