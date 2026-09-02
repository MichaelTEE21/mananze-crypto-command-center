"""Persist Intelligence Report observations for What-changed? comparisons."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now
from mccc.paths import ensure_dirs


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS intelligence_report_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    query_key TEXT NOT NULL,
    chain TEXT,
    snapshot_json TEXT NOT NULL,
    confidence TEXT,
    data_mode TEXT,
    is_demo INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_iro_query
    ON intelligence_report_observations(entity_type, query_key, chain, created_at);
"""


class ReportRepository:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        ensure_dirs()
        self.db_path = db_path

    def ensure_schema(self) -> None:
        with connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)

    def save_observation(
        self,
        *,
        report_id: str,
        entity_type: str,
        query_key: str,
        chain: str,
        snapshot: dict[str, Any],
        confidence: str,
        data_mode: str,
        is_demo: bool = False,
    ) -> int:
        self.ensure_schema()
        with connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO intelligence_report_observations
                (report_id, entity_type, query_key, chain, snapshot_json, confidence, data_mode, is_demo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    entity_type,
                    query_key.lower(),
                    chain,
                    json.dumps(snapshot, default=str),
                    confidence,
                    data_mode,
                    1 if is_demo else 0,
                    utc_now(),
                ),
            )
            return int(cur.lastrowid)

    def previous_observation(
        self,
        *,
        entity_type: str,
        query_key: str,
        chain: str = "",
        before_report_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        self.ensure_schema()
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM intelligence_report_observations
                WHERE entity_type = ? AND query_key = ?
                  AND (? = '' OR chain = ?)
                ORDER BY id DESC
                LIMIT 5
                """,
                (entity_type, query_key.lower(), chain or "", chain or ""),
            ).fetchall()
        for row in rows:
            d = dict(row)
            if before_report_id and d.get("report_id") == before_report_id:
                continue
            try:
                snap = json.loads(d.get("snapshot_json") or "{}")
            except json.JSONDecodeError:
                snap = {}
            snap["created_at"] = d.get("created_at")
            snap["report_id"] = d.get("report_id")
            snap["confidence"] = d.get("confidence")
            snap["data_mode"] = d.get("data_mode")
            return snap
        return None
