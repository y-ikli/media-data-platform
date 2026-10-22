from datetime import date

import pytest

from adsdata.ingestion.dates import DateWindow
from adsdata.simulation import google_ads, meta_ads
from adsdata.simulation.generator import Campaign, generate, seeded_rng

WEEK = DateWindow(date(2026, 10, 1), date(2026, 10, 7))


def _no_extra(rng, impressions, clicks):
    return {}


def test_same_inputs_give_the_same_rows():
    campaigns = [Campaign("c1", "Une"), Campaign("c2", "Deux")]

    assert generate("s", campaigns, WEEK, _no_extra) == generate("s", campaigns, WEEK, _no_extra)


def test_another_seed_gives_other_values():
    first, second = seeded_rng("a", "c1", "2026-10-01"), seeded_rng("b", "c1", "2026-10-01")

    assert first.random() != second.random()


def test_one_row_per_campaign_and_day_with_clicks_below_impressions():
    campaigns = [Campaign("c1", "Une"), Campaign("c2", "Deux")]

    rows = generate("s", campaigns, WEEK, _no_extra)

    assert len(rows) == 2 * WEEK.days_count
    assert {(r["date"], r["campaign_id"]) for r in rows} == {
        (d.isoformat(), c.campaign_id) for d in WEEK.days() for c in campaigns
    }
    assert all(0 < r["clicks"] <= r["impressions"] for r in rows)


def test_a_day_does_not_depend_on_the_rest_of_the_window():
    one_day = DateWindow(date(2026, 10, 3), date(2026, 10, 3))
    campaigns = [Campaign("c1", "Une")]

    in_week = [r for r in generate("s", campaigns, WEEK, _no_extra) if r["date"] == "2026-10-03"]

    assert generate("s", campaigns, one_day, _no_extra) == in_week


@pytest.mark.parametrize("api", [google_ads, meta_ads], ids=["google_ads", "meta_ads"])
def test_simulated_apis_cover_every_campaign_every_day(api):
    rows = api.campaign_daily(WEEK)

    assert len(rows) == len(api.CAMPAIGNS) * WEEK.days_count


def test_google_ads_costs_are_integer_micros_in_euros():
    rows = google_ads.campaign_daily(WEEK)

    assert all(isinstance(r["cost_micros"], int) and r["cost_micros"] > 0 for r in rows)
    assert {r["currency_code"] for r in rows} == {"EUR"}


def test_meta_ads_spend_is_in_the_account_currency():
    rows = meta_ads.campaign_daily(WEEK)

    assert all(isinstance(r["spend"], float) for r in rows)
    assert {r["account_currency"] for r in rows} == {"EUR"}
