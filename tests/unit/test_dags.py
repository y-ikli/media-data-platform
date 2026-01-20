"""Unit tests for DAG validation."""

import ast
from pathlib import Path

import pytest


def test_dags_directory_exists():
    """Test that dags directory exists."""
    dags_dir = Path(__file__).resolve().parents[2] / "dags"
    assert dags_dir.exists()
    assert dags_dir.is_dir()


def test_all_dags_are_valid_python():
    """Test that all DAG files have valid Python syntax."""
    dags_dir = Path(__file__).resolve().parents[2] / "dags"
    dag_files = list(dags_dir.glob("*.py"))
    
    assert len(dag_files) >= 3, "Expected at least 3 DAG files"
    
    for dag_file in dag_files:
        with open(dag_file, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {dag_file.name}: {e}")


def test_dags_contain_dag_decorator():
    """Test that DAG files contain @dag decorator or DAG class."""
    dags_dir = Path(__file__).resolve().parents[2] / "dags"
    
    for dag_file in dags_dir.glob("*.py"):
        with open(dag_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Skip if it's __init__.py or similar
        if dag_file.name.startswith('_'):
            continue
            
        # Should contain either @dag or DAG( instantiation
        has_dag_decorator = '@dag' in content
        has_dag_class = 'DAG(' in content
        
        assert has_dag_decorator or has_dag_class, \
            f"{dag_file.name} should contain @dag decorator or DAG class"


def test_marketing_platform_dag_structure():
    """Test that marketing_data_platform DAG has expected structure."""
    dag_file = Path(__file__).resolve().parents[2] / "dags" / "marketing_data_platform.py"
    
    if not dag_file.exists():
        pytest.skip("marketing_data_platform.py not found")
    
    with open(dag_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key tasks
    expected_tasks = [
        'extract_google_ads',
        'extract_meta_ads',
        'dbt_run',
        'dbt_test',
        'volume_check',
        'summary'
    ]
    
    for task in expected_tasks:
        assert task in content, f"Expected task '{task}' not found in DAG"
