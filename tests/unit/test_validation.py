import math

import pytest

from adsdata.ingestion.schemas import GOOGLE_ADS, META_ADS, BigQueryType
from adsdata.ingestion.validation import DataQualityError, matches_type, validate_rows


def rejected(rows, spec, window, **kwargs) -> tuple[str, ...]:
    with pytest.raises(DataQualityError) as exc_info:
        validate_rows(rows, spec, window, **kwargs)
    return exc_info.value.errors


@pytest.mark.parametrize("spec", [GOOGLE_ADS, META_ADS], ids=["google_ads", "meta_ads"])
def test_valid_batch_passes(spec, make_row, window):
    rows = [make_row(spec), make_row(spec, campaign_id="c2"), make_row(spec, date="2026-10-07")]

    validate_rows(rows, spec, window)


def test_empty_batch_is_valid(window):
    validate_rows([], GOOGLE_ADS, window)


def test_optional_columns_may_be_null_or_absent(make_row, window):
    row = make_row(conversions=None)
    del row["campaign_name"]

    validate_rows([row], GOOGLE_ADS, window)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"inattendue": 1}, "colonnes inconnues ['inattendue']"),
        ({"campaign_id": None}, "campaign_id manquant"),
        ({"impressions": "1000"}, "impressions : '1000' n'est pas un INT64"),
        ({"impressions": True}, "impressions : True n'est pas un INT64"),
        ({"clicks": 5.0}, "clicks : 5.0 n'est pas un INT64"),
        ({"conversions": math.nan}, "conversions : nan n'est pas un FLOAT64"),
        ({"date": "01/10/2026"}, "date : '01/10/2026' n'est pas un DATE"),
        ({"ingested_at": "hier"}, "ingested_at : 'hier' n'est pas un TIMESTAMP"),
        ({"campaign_id": 42}, "campaign_id : 42 n'est pas un STRING"),
        ({"data_mode": "test"}, "data_mode : 'test' hors de ['real', 'simulated']"),
        ({"date": "2026-09-30"}, "date 2026-09-30 hors de la fenêtre 2026-10-01..2026-10-07"),
        ({"cost_micros": -1}, "cost_micros négatif (-1)"),
        ({"conversion_value": -0.5}, "conversion_value négatif (-0.5)"),
        ({"clicks": 1001}, "clicks (1001) > impressions (1000)"),
    ],
)
def test_each_rule_reports_its_error(overrides, expected, make_row, window):
    errors = rejected([make_row(**overrides)], GOOGLE_ADS, window)

    assert len(errors) == 1
    assert errors[0] == f"ligne 0 : {expected}"


def test_absent_required_column_is_reported(make_row, window):
    row = make_row()
    del row["currency_code"]

    assert rejected([row], GOOGLE_ADS, window) == ("ligne 0 : currency_code manquant",)


def test_duplicate_campaign_and_day_is_reported(make_row, window):
    rows = [make_row(), make_row(campaign_id="c2"), make_row()]

    errors = rejected(rows, GOOGLE_ADS, window)

    assert errors == ("ligne 2 : doublon sur ('date', 'campaign_id') = ('2026-10-01', 'c1')",)


def test_all_errors_are_reported_together(make_row, window):
    rows = [make_row(clicks=-1), make_row(campaign_id="c2", data_mode="faux")]

    errors = rejected(rows, GOOGLE_ADS, window)

    assert [e.split(" : ")[0] for e in errors] == ["ligne 0", "ligne 1"]


def test_error_count_is_capped(make_row, window):
    rows = [make_row(campaign_id=f"c{i}", clicks=-1) for i in range(5)]

    errors = rejected(rows, GOOGLE_ADS, window, max_errors=3)

    assert len(errors) == 4
    assert errors[-1] == "… arrêt après 3 erreurs"


def test_max_errors_must_be_positive(window):
    with pytest.raises(ValueError, match="max_errors"):
        validate_rows([], GOOGLE_ADS, window, max_errors=0)


def test_exception_message_lists_every_error(make_row, window):
    with pytest.raises(DataQualityError, match=r"Lot rejeté :\n  - ligne 0 : clicks négatif"):
        validate_rows([make_row(clicks=-1)], GOOGLE_ADS, window)


@pytest.mark.parametrize(
    ("value", "bq_type", "expected"),
    [
        (3, BigQueryType.INT64, True),
        (3, BigQueryType.FLOAT64, True),
        (3.5, BigQueryType.FLOAT64, True),
        (math.inf, BigQueryType.FLOAT64, False),
        (False, BigQueryType.INT64, False),
        ("x", BigQueryType.STRING, True),
        ("2026-10-01", BigQueryType.DATE, True),
        (20261001, BigQueryType.DATE, False),
        ("2026-10-01T06:00:00+00:00", BigQueryType.TIMESTAMP, True),
        (20261001, BigQueryType.TIMESTAMP, False),
    ],
)
def test_matches_type(value, bq_type, expected):
    assert matches_type(value, bq_type) is expected
