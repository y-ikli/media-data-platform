from mdp.fake_apis.google_ads_api import get_campaign_daily as google
from mdp.fake_apis.meta_ads_api import get_campaign_daily as meta


def test_generation_is_deterministic():
    assert google("2024-01-01", "2024-01-10") == google("2024-01-01", "2024-01-10")
    assert meta("2024-01-01", "2024-01-10") == meta("2024-01-01", "2024-01-10")


def test_a_day_does_not_depend_on_the_requested_range():
    """Rejouer une sous-plage redonne les mêmes valeurs : condition de l'idempotence."""
    full = {(r["date"], r["campaign_id"]): r for r in google("2024-01-01", "2024-01-31")}
    part = google("2024-01-10", "2024-01-12")
    assert part and all(full[(r["date"], r["campaign_id"])] == r for r in part)


def test_one_row_per_campaign_and_day_inclusive_bounds():
    rows = meta("2024-02-28", "2024-03-01")  # 2024 bissextile : 3 jours
    assert len(rows) == 3 * 4 and {r["date"] for r in rows} == {"2024-02-28", "2024-02-29", "2024-03-01"}


def test_invariants_hold_over_a_long_range():
    for r in google("2023-01-01", "2023-12-31") + meta("2023-01-01", "2023-12-31"):
        assert 0 <= r["clicks"] <= r["impressions"]
        assert r["conversions"] <= r["clicks"] and r["conversion_value"] >= 0


def test_sources_have_their_own_spend_column():
    assert "cost_usd" in google("2024-01-01", "2024-01-01")[0] and "spend_usd" in meta("2024-01-01", "2024-01-01")[0]
