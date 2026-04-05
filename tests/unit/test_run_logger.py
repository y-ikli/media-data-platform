"""Unit tests for monitoring run_logger module."""

import inspect
import sys
from unittest.mock import MagicMock

# Mock google.cloud.bigquery before importing run_logger (not installed locally)
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.bigquery'] = MagicMock()

from src.monitoring import run_logger  # noqa: E402
from src.monitoring.run_logger import get_recent_runs, log_run_summary  # noqa: E402


def test_run_logger_module_imports():
    """Test that run_logger module can be imported."""
    assert hasattr(run_logger, 'log_run_summary')
    assert hasattr(run_logger, 'get_recent_runs')


def test_log_run_summary_signature():
    """Test that log_run_summary has expected parameters."""
    sig = inspect.signature(log_run_summary)
    params = list(sig.parameters.keys())

    # log_run_summary now takes project_id + a RunSummary dataclass
    assert 'project_id' in params
    assert 'summary' in params


def test_get_recent_runs_signature():
    """Test that get_recent_runs has expected parameters."""
    sig = inspect.signature(get_recent_runs)
    params = list(sig.parameters.keys())

    assert 'project_id' in params
    assert 'limit' in params
