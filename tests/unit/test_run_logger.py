"""Unit tests for monitoring run_logger module."""

import inspect

from src.monitoring import run_logger
from src.monitoring.run_logger import get_recent_runs, log_run_summary


def test_run_logger_module_imports():
    """Test that run_logger module can be imported."""
    assert hasattr(run_logger, 'log_run_summary')
    assert hasattr(run_logger, 'get_recent_runs')


def test_log_run_summary_signature():
    """Test that log_run_summary has expected parameters."""
    sig = inspect.signature(log_run_summary)
    params = list(sig.parameters.keys())
    
    expected_params = [
        'project_id',
        'run_id',
        'dag_id',
        'run_date',
        'execution_date',
        'status',
        'google_ads_result',
        'meta_ads_result'
    ]
    
    for param in expected_params:
        assert param in params, f"Expected parameter '{param}' not found"


def test_get_recent_runs_signature():
    """Test that get_recent_runs has expected parameters."""
    sig = inspect.signature(get_recent_runs)
    params = list(sig.parameters.keys())
    
    assert 'project_id' in params
    assert 'limit' in params
