from datetime import date

import pytest

from mdp.ingestion.schemas import GOOGLE_ADS
from mdp.ingestion.validation import DataQualityError, parse_date, validate_rows

START, END = date(2024, 1, 1), date(2024, 1, 31)


def row(**over):
    base = {
        "date": "2024-01-05",
        "campaign_id": "c1",
        "campaign_name": "n",
        "impressions": 100,
        "clicks": 10,
        "conversions": 1,
        "conversion_value": 50.0,
        "cost_usd": 12.5,
        "ingested_at": "2024-02-01T00:00:00+00:00",
        "extract_run_id": "r",
        "source": "google_ads",
        "data_mode": "simulated",
    }
    return {**base, **over}


def test_valid_batch_passes():
    validate_rows([row(), row(campaign_id="c2")], GOOGLE_ADS, START, END)


@pytest.mark.parametrize(
    "bad,fragment",
    [
        (row(date="2024-02-01"), "hors de la fenêtre"),
        (row(date="05/01/2024"), "Date invalide"),
        (row(campaign_id=None), "campaign_id manquant"),
        (row(clicks=-1), "négatif"),
        (row(clicks=500), "clicks (500) > impressions"),
        (row(surprise=1), "colonnes inconnues"),
    ],
)
def test_invalid_rows_are_rejected_with_a_clear_reason(bad, fragment):
    with pytest.raises(DataQualityError, match=fragment.replace("(", r"\(").replace(")", r"\)")):
        validate_rows([bad], GOOGLE_ADS, START, END)


def test_duplicate_key_is_rejected():
    with pytest.raises(DataQualityError, match="doublon"):
        validate_rows([row(), row()], GOOGLE_ADS, START, END)


def test_all_errors_are_reported_together():
    with pytest.raises(DataQualityError) as exc:
        validate_rows([row(clicks=-1), row(campaign_id="c2", cost_usd=None)], GOOGLE_ADS, START, END)
    assert "négatif" in str(exc.value) and "cost_usd manquant" in str(exc.value)


def test_parse_date():
    assert parse_date("2024-02-29") == date(2024, 2, 29)
    with pytest.raises(DataQualityError):
        parse_date("2023-02-29")
