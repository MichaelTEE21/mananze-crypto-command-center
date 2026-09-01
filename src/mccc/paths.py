"""Path helpers for MCCC data and content."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
CONTENT_DIR = ROOT / "content"
DB_PATH = DATA_DIR / "mccc.db"
EDUCATION_DIR = CONTENT_DIR / "education"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EDUCATION_DIR.mkdir(parents=True, exist_ok=True)
