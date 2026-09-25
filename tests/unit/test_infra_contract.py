"""Le code Terraform et le code Python doivent rester d'accord : arguments des jobs, variables d'environnement."""

import re
from pathlib import Path

import pytest

from mdp.ingestion.cli import build_parser, resolve_window

INFRA = Path(__file__).resolve().parents[2] / "infra"
RUN_JOBS = (INFRA / "run_jobs.tf").read_text(encoding="utf-8")
SRC = Path(__file__).resolve().parents[2] / "src"


def _ingest_args() -> list[list[str]]:
    """Listes `args = [...]` des jobs d'ingestion, avec les références Terraform remplacées par des valeurs."""
    found = re.findall(r'args\s*=\s*\[(.*?"--source".*?)\]', RUN_JOBS, re.S)
    out = []
    for raw in found:
        raw = raw.replace("var.meta_mode", '"simulated"').replace("tostring(var.lookback_days)", '"3"')
        out.append(re.findall(r'"([^"]*)"', raw))
    return out


def test_two_ingestion_jobs_are_defined():
    assert len(_ingest_args()) == 2


@pytest.mark.parametrize("args", _ingest_args())
def test_job_arguments_are_accepted_by_the_cli(args):
    parsed = build_parser().parse_args(args)
    start, end = resolve_window(parsed)
    assert parsed.source in {"meta_ads", "google_ads"} and start <= end


def test_google_job_is_always_simulated():
    google = next(a for a in _ingest_args() if "google_ads" in a)
    assert google[google.index("--mode") + 1] == "simulated"


def test_every_environment_variable_set_by_terraform_is_read_by_the_code():
    code = "\n".join(p.read_text(encoding="utf-8") for p in SRC.rglob("*.py"))
    profiles = (Path(__file__).resolve().parents[2] / "dbt/mdp/profiles.yml").read_text(encoding="utf-8")
    names = set(re.findall(r"^\s+([A-Z][A-Z0-9_]+)\s*=", RUN_JOBS, re.M))
    names |= {"DBT_TARGET"}
    assert {"GCP_PROJECT_ID", "BQ_LOCATION", "BQ_RAW_DATASET", "META_ADS_APP_ID", "META_ADS_ACCESS_TOKEN"} <= names
    for name in names - {"DBT_TARGET"}:
        assert name in code, f"{name} est défini par Terraform mais lu nulle part"
    assert "DBT_TARGET" in profiles


def test_workflow_runs_the_three_jobs_and_dbt_comes_last():
    text = (INFRA / "templates" / "daily.yaml.tftpl").read_text(encoding="utf-8")
    for job in ("meta_job", "google_job", "dbt_job"):
        assert "${" + job + "}" in text
    assert text.index("${meta_job}") < text.index("${dbt_job}") and text.index("${google_job}") < text.index("${dbt_job}")


def test_terraform_never_writes_a_secret_value():
    secrets = (INFRA / "secrets.tf").read_text(encoding="utf-8")
    assert "google_secret_manager_secret_version" not in secrets and "secret_data" not in secrets
    assert "credentials" not in (INFRA / "versions.tf").read_text(encoding="utf-8")


def test_workload_identity_is_restricted_to_a_repository_and_a_ref():
    wif = (INFRA / "wif.tf").read_text(encoding="utf-8")
    assert "attribute_condition" in wif and "assertion.repository ==" in wif and "assertion.ref ==" in wif
