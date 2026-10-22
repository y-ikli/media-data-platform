import pytest

from adsdata.config import DEFAULT_LOCATION, DEFAULT_RAW_DATASET, ConfigError, Settings


def test_defaults_apply_when_only_the_project_is_set():
    settings = Settings.from_env({"GCP_PROJECT_ID": "mon-projet"})

    assert settings == Settings("mon-projet", DEFAULT_LOCATION, DEFAULT_RAW_DATASET)


def test_every_value_can_be_overridden():
    env = {"GCP_PROJECT_ID": "p", "BQ_LOCATION": "europe-west9", "BQ_RAW_DATASET": "raw_test"}

    assert Settings.from_env(env) == Settings("p", "europe-west9", "raw_test")


@pytest.mark.parametrize("env", [{}, {"GCP_PROJECT_ID": ""}, {"GCP_PROJECT_ID": "   "}])
def test_missing_or_blank_project_is_an_error(env):
    with pytest.raises(ConfigError, match="GCP_PROJECT_ID"):
        Settings.from_env(env)


def test_blank_optional_values_fall_back_to_defaults():
    env = {"GCP_PROJECT_ID": "p", "BQ_LOCATION": "", "BQ_RAW_DATASET": " "}

    assert Settings.from_env(env) == Settings("p")


def test_reads_process_environment_by_default(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "depuis-env")
    monkeypatch.delenv("BQ_LOCATION", raising=False)

    assert Settings.from_env().project_id == "depuis-env"


def test_settings_are_immutable():
    settings = Settings("p")

    with pytest.raises(AttributeError):
        settings.project_id = "autre"  # type: ignore[misc]
