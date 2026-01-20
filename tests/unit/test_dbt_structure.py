"""Unit tests for dbt models structure."""

from pathlib import Path
import yaml  # type: ignore[import]


def test_dbt_project_yml_exists():
    """Test that dbt_project.yml exists."""
    dbt_dir = Path(__file__).resolve().parents[2] / "dbt" / "mdp"
    dbt_project = dbt_dir / "dbt_project.yml"
    
    assert dbt_project.exists(), "dbt_project.yml not found"


def test_dbt_project_yml_valid():
    """Test that dbt_project.yml is valid YAML."""
    dbt_dir = Path(__file__).resolve().parents[2] / "dbt" / "mdp"
    dbt_project = dbt_dir / "dbt_project.yml"
    
    with open(dbt_project, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    assert 'name' in config
    assert 'version' in config
    assert 'models' in config


def test_staging_models_exist():
    """Test that staging models directory exists."""
    staging_dir = Path(__file__).resolve().parents[2] / "dbt" / "mdp" / "models" / "staging"
    
    assert staging_dir.exists(), "Staging models directory not found"
    
    # Should have at least 2 staging models (google_ads + meta_ads)
    sql_files = list(staging_dir.glob("**/*.sql"))
    assert len(sql_files) >= 2, "Expected at least 2 staging models"


def test_marts_models_exist():
    """Test that marts models directory exists."""
    marts_dir = Path(__file__).resolve().parents[2] / "dbt" / "mdp" / "models" / "marts"
    
    assert marts_dir.exists(), "Marts models directory not found"
    
    # Should have mart_campaign_daily
    mart_file = marts_dir / "mart_campaign_daily.sql"
    assert mart_file.exists(), "mart_campaign_daily.sql not found"


def test_models_have_yml_files():
    """Test that model directories have schema.yml files."""
    models_dir = Path(__file__).resolve().parents[2] / "dbt" / "mdp" / "models"
    
    for subdir in ['staging', 'intermediate', 'marts']:
        subdir_path = models_dir / subdir
        if subdir_path.exists():
            yml_files = list(subdir_path.glob("*.yml")) + list(subdir_path.glob("**/*.yml"))
            assert len(yml_files) > 0, f"No .yml files found in {subdir}"


def test_dbt_tests_directory_exists():
    """Test that dbt tests directory exists."""
    tests_dir = Path(__file__).resolve().parents[2] / "dbt" / "mdp" / "tests"
    
    assert tests_dir.exists(), "dbt tests directory not found"
    
    # Should have custom SQL tests
    sql_tests = list(tests_dir.glob("*.sql"))
    assert len(sql_tests) >= 3, "Expected at least 3 custom SQL tests"
