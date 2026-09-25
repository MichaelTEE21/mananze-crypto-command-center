"""Pytest fixtures for Mananze Hub Crypto/Web3."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mananze_hub.crypto_web3.db import init_db  # noqa: E402


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "test_mananze_hub.db"
    init_db(path)
    return path
