"""Pytest fixtures for MCCC."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mccc.db import init_db  # noqa: E402


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "test_mccc.db"
    init_db(path)
    return path
