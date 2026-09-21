"""dbt exécuté pour de vrai sur DuckDB (sans identifiants) : modèles, tests de données, tests unitaires, incrémental."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from mdp.dev.duckdb_fixtures import build

pytestmark = pytest.mark.dbt
ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "dbt" / "mdp"


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("dbt")
    db = tmp / "ci.duckdb"
    build(db)
    return {
        **os.environ,
        "DBT_TARGET": "duckdb",
        "DBT_DUCKDB_PATH": str(db),
        "DBT_PROFILES_DIR": str(PROJECT),
        "DBT_TARGET_PATH": str(tmp / "target"),
        "DBT_LOG_PATH": str(tmp / "logs"),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
    }


def dbt(env, *args, check=True):
    exe = shutil.which("dbt", path=str(Path(sys.executable).parent)) or "dbt"
    res = subprocess.run([exe, *args, "--project-dir", str(PROJECT)], env=env, capture_output=True, text=True, cwd=PROJECT)
    if check and res.returncode != 0:
        pytest.fail(f"dbt {' '.join(args)} a échoué :\n{res.stdout[-3000:]}\n{res.stderr[-1000:]}")
    return res


def query(env, sql):
    con = duckdb.connect(env["DBT_DUCKDB_PATH"], read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


@pytest.fixture(scope="module", autouse=True)
def deps(env):
    dbt(env, "deps")


def test_full_build_passes_every_model_data_test_and_unit_test(env):
    res = dbt(env, "build")
    assert "ERROR=0" in res.stdout and "WARN=0" in res.stdout, res.stdout[-1500:]
    assert "PASS=" in res.stdout


def test_reingested_days_do_not_duplicate_the_grain(env):
    (n_raw,) = query(env, "select count(*) from mdp_raw.meta_ads_campaign_daily")[0]
    (n_mart,) = query(env, "select count(*) from mdp_marts.mart_campaign_daily where platform = 'meta_ads'")[0]
    assert n_raw > n_mart, "le raw contient des réingestions que le mart doit avoir dédupliquées"
    assert n_mart == 91 * 4  # 91 jours (jan-mars 2024) × 4 campagnes


def test_latest_ingestion_wins(env):
    """Janvier a été rechargé avec des chiffres révisés (×0,9) : le mart doit refléter la révision."""
    rows = query(
        env,
        """
        select m.impressions, r.impressions
        from mdp_marts.mart_campaign_daily m
        join (select date, campaign_id, impressions, row_number() over (partition by date, campaign_id order by ingested_at) rn
              from mdp_raw.meta_ads_campaign_daily) r
          on r.date = m.report_date and r.campaign_id = m.campaign_id and r.rn = 1
        where m.platform = 'meta_ads' and m.report_date = date '2024-01-15'
    """,
    )
    assert rows and all(mart < first for mart, first in rows)


def test_simulated_data_is_labelled_everywhere(env):
    assert query(env, "select distinct data_mode from mdp_marts.mart_campaign_daily") == [("simulated",)]
    assert query(env, "select distinct data_mode from mdp_marts.mart_platform_monthly") == [("simulated",)]


def _late_correction(env, day, factor):
    """Insère une nouvelle ingestion de ``day`` (Meta) dont les impressions sont multipliées par ``factor``."""
    con = duckdb.connect(env["DBT_DUCKDB_PATH"])
    con.execute(f"""
        insert into mdp_raw.meta_ads_campaign_daily
        select * replace (cast(impressions * {factor} as bigint) as impressions,
                          least(clicks, cast(impressions * {factor} as bigint)) as clicks,
                          timestamptz '2024-05-01 00:00:00+00' as ingested_at, 'late-fix' as extract_run_id)
        from mdp_raw.meta_ads_campaign_daily where date = date '{day}' and extract_run_id != 'late-fix'
    """)
    con.close()


def _impressions(env, day):
    return query(
        env,
        f"select sum(impressions) from mdp_marts.mart_campaign_daily where platform='meta_ads' and report_date = date '{day}'",
    )[0][0]


def test_incremental_reprocesses_the_lookback_window_only(env):
    dbt(env, "run", "-s", "mart_campaign_daily")
    recent_before, old_before = _impressions(env, "2024-03-29"), _impressions(env, "2024-01-20")
    _late_correction(env, "2024-03-29", 2)  # dans la fenêtre glissante (7 jours avant le 31 mars)
    _late_correction(env, "2024-01-20", 2)  # hors fenêtre
    dbt(env, "run", "-s", "mart_campaign_daily")
    assert _impressions(env, "2024-03-29") == pytest.approx(recent_before * 2, rel=0.001)
    assert _impressions(env, "2024-01-20") == old_before, "hors fenêtre : inchangé tant qu'on ne demande pas de retraitement"


def test_reprocess_from_and_full_refresh_converge(env):
    dbt(env, "run", "-s", "mart_campaign_daily", "--vars", "{reprocess_from: '2024-01-01'}")
    after_reprocess = query(
        env, "select report_date, platform, campaign_id, impressions from mdp_marts.mart_campaign_daily order by 1, 2, 3"
    )
    dbt(env, "run", "-s", "mart_campaign_daily", "--full-refresh")
    after_full = query(
        env, "select report_date, platform, campaign_id, impressions from mdp_marts.mart_campaign_daily order by 1, 2, 3"
    )
    assert after_reprocess == after_full
    assert query(
        env,
        "select count(*) from (select 1 from mdp_marts.mart_campaign_daily "
        "group by report_date, platform, campaign_id having count(*) > 1)",
    ) == [(0,)]
