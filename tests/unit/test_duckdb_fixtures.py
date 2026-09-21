import duckdb

from mdp.dev.duckdb_fixtures import build


def test_build_creates_raw_tables_with_reingestion(tmp_path):
    counts = build(tmp_path / "raw.duckdb", "2024-01-01", "2024-02-29")
    assert counts == {"google_ads_campaign_daily": 60 * 5 + 31 * 5, "meta_ads_campaign_daily": 60 * 4 + 31 * 4}
    con = duckdb.connect(str(tmp_path / "raw.duckdb"), read_only=True)
    dup = con.execute(
        "select count(*) from (select 1 from mdp_raw.meta_ads_campaign_daily group by date, campaign_id having count(*) > 1)"
    ).fetchone()[0]
    assert dup == 31 * 4  # janvier chargé deux fois
    assert con.execute("select distinct data_mode from mdp_raw.google_ads_campaign_daily").fetchall() == [("simulated",)]


def test_build_without_reingestion_has_no_duplicates(tmp_path):
    counts = build(tmp_path / "raw.duckdb", "2024-01-01", "2024-01-10", with_reingestion=False)
    assert counts["meta_ads_campaign_daily"] == 40
