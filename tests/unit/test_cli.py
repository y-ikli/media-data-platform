import json
from datetime import date

import pytest

from mdp.ingestion.cli import build_parser, main, resolve_window


def test_dry_run_needs_no_credentials(capsys, monkeypatch, caplog):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    with caplog.at_level("INFO"):
        assert main(["--source", "google_ads", "--start", "2024-01-01", "--end", "2024-01-03", "--dry-run"]) == 0
    reports = [json.loads(r.message.split("ingestion ", 1)[1]) for r in caplog.records if r.message.startswith("ingestion ")]
    assert reports[0]["rows"] == 15 and reports[0]["dry_run"] is True


def test_missing_project_is_a_clean_error(monkeypatch, caplog):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    assert main(["--source", "meta_ads", "--start", "2024-01-01", "--end", "2024-01-02"]) == 2
    assert "GCP_PROJECT_ID" in caplog.text


def test_real_google_is_a_clean_error(caplog):
    assert main(["--source", "google_ads", "--mode", "real", "--start", "2024-01-01", "--end", "2024-01-02", "--dry-run"]) == 2


def test_bad_dates_are_a_clean_error():
    assert main(["--source", "meta_ads", "--start", "2024-13-01", "--end", "2024-01-02", "--dry-run"]) == 2


def test_parser_defaults_to_simulated():
    assert build_parser().parse_args(["--source", "meta_ads", "--start", "a", "--end", "b"]).mode == "simulated"


def test_unknown_source_exits():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--source", "tiktok", "--start", "a", "--end", "b"])


def test_lookback_window_ends_yesterday():
    args = build_parser().parse_args(["--source", "meta_ads", "--lookback-days", "3"])
    assert resolve_window(args, today=date(2024, 3, 10)) == ("2024-03-07", "2024-03-09")


def test_lookback_of_one_is_yesterday_only():
    args = build_parser().parse_args(["--source", "meta_ads", "--lookback-days", "1"])
    assert resolve_window(args, today=date(2024, 3, 1)) == ("2024-02-29", "2024-02-29")


def test_lookback_conflicts_with_explicit_bounds_and_needs_a_window(caplog):
    assert main(["--source", "meta_ads", "--lookback-days", "3", "--start", "2024-01-01", "--dry-run"]) == 2
    assert main(["--source", "meta_ads", "--dry-run"]) == 2
    assert main(["--source", "meta_ads", "--lookback-days", "0", "--dry-run"]) == 2


def test_scheduled_run_end_to_end_dry_run(caplog):
    with caplog.at_level("INFO"):
        assert main(["--source", "google_ads", "--lookback-days", "2", "--dry-run"]) == 0
    assert "2 lignes" not in caplog.text and "10 lignes" in caplog.text  # 2 jours × 5 campagnes
