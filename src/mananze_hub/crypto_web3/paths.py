"""Path helpers for MCCC data and content."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("MCCC_DATA_DIR", str(ROOT / "data"))).expanduser()
CONTENT_DIR = ROOT / "content"
# Prefer explicit sqlite path for container/volume mounts. DATABASE_URL (Postgres) is Phase 2+.
_db_env = os.environ.get("MCCC_DB_PATH", "").strip()
DB_PATH = Path(_db_env).expanduser() if _db_env else (DATA_DIR / "mccc.db")
EDUCATION_DIR = CONTENT_DIR / "education"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EDUCATION_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
