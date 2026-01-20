"""Unit tests configuration and fixtures."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "dags"))
