"""IntelligenceRepository — SQLite locally; interface ready for durable production DB.

NOTE: Local SQLite / filesystem is fine for desktop MCCC. It is NOT durable on
ephemeral hosts (e.g. Vercel). Production should swap the store behind this repo.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from mccc.db import connect, utc_now
from mccc.intelligence.schema import (
    CandidateProject,
    CandidateProjectStatus,
    EventStatus,
    FundingRecord,
    IntelligenceEvent,
    NOT_DISCLOSED,
    UNKNOWN,
)

INTELLIGENCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS intelligence_sources (
    key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tier INTEGER NOT NULL DEFAULT 5,
    source_type TEXT NOT NULL DEFAULT 'rss',
    feed_url TEXT DEFAULT '',
    homepage TEXT DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    min_interval_seconds INTEGER NOT NULL DEFAULT 900,
    notes TEXT DEFAULT '',
    last_success_at TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intelligence_events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT DEFAULT '',
    category TEXT NOT NULL,
    subcategory TEXT DEFAULT '',
    project TEXT DEFAULT 'Unknown',
    token TEXT DEFAULT 'Unknown',
    blockchain TEXT DEFAULT 'Unknown',
    source TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    source_type TEXT DEFAULT 'rss',
    published_at TEXT DEFAULT '',
    discovered_at TEXT DEFAULT '',
    confidence TEXT DEFAULT 'UNCONFIRMED',
    importance INTEGER DEFAULT 40,
    sentiment TEXT DEFAULT 'neutral',
    entities TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    status TEXT DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL,
    discovery_latency_seconds REAL,
    related_sources TEXT DEFAULT '[]',
    fingerprint TEXT DEFAULT '',
    cluster_id TEXT DEFAULT '',
    source_tier INTEGER DEFAULT 5,
    why_it_matters TEXT DEFAULT '',
    what_happened TEXT DEFAULT '',
    airdrop_signal_status TEXT DEFAULT '',
    is_demo INTEGER NOT NULL DEFAULT 0,
    raw_text TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_intel_events_category ON intelligence_events(category);
CREATE INDEX IF NOT EXISTS idx_intel_events_status ON intelligence_events(status);
CREATE INDEX IF NOT EXISTS idx_intel_events_fp ON intelligence_events(fingerprint);
CREATE INDEX IF NOT EXISTS idx_intel_events_demo ON intelligence_events(is_demo);
CREATE INDEX IF NOT EXISTS idx_intel_events_published ON intelligence_events(published_at);
CREATE INDEX IF NOT EXISTS idx_intel_events_importance ON intelligence_events(importance);

CREATE TABLE IF NOT EXISTS funding_rounds (
    id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    amount TEXT DEFAULT 'Not disclosed',
    currency TEXT DEFAULT 'USD',
    round_type TEXT DEFAULT 'Unknown',
    announced_at TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    confidence TEXT DEFAULT 'UNCONFIRMED',
    notes TEXT DEFAULT '',
    is_demo INTEGER NOT NULL DEFAULT 0,
    investors_json TEXT DEFAULT '[]',
    event_id TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_funding_project ON funding_rounds(project);

CREATE TABLE IF NOT EXISTS intelligence_candidates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    blockchain TEXT DEFAULT 'Unknown',
    website TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    source_event_id TEXT DEFAULT '',
    linked_project_id INTEGER,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_intel_cand_status ON intelligence_candidates(status);

CREATE TABLE IF NOT EXISTS narratives (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    summary TEXT DEFAULT '',
    tags TEXT DEFAULT '[]',
    is_demo INTEGER NOT NULL DEFAULT 0,
    heat INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intelligence_watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ref_type TEXT NOT NULL DEFAULT 'event',
    ref_id TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_intel_watch_user ON intelligence_watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_intel_watch_ref ON intelligence_watchlist(ref_type, ref_id);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'running',
    sources_json TEXT DEFAULT '[]',
    docs_ingested INTEGER DEFAULT 0,
    docs_stored INTEGER DEFAULT 0,
    docs_deduped INTEGER DEFAULT 0,
    error TEXT DEFAULT '',
    meta_json TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_started ON ingestion_runs(started_at);
"""


def compute_discovery_latency_seconds(published_at: str, discovered_at: str) -> Optional[float]:
    """discovered_at - published_at in seconds; None if either unparseable."""
    if not published_at or not discovered_at:
        return None
    try:
        pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        disc = datetime.fromisoformat(discovered_at.replace("Z", "+00:00"))
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        if disc.tzinfo is None:
            disc = disc.replace(tzinfo=timezone.utc)
        return max(0.0, (disc - pub).total_seconds())
    except Exception:
        return None


class IntelligenceRepository:
    """Persistence facade for the intelligence engine (not a chatbot)."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path

    def ensure_schema(self) -> None:
        with connect(self.db_path) as conn:
            conn.executescript(INTELLIGENCE_SCHEMA)

    # --- events ---
    def upsert_event(self, event: IntelligenceEvent) -> str:
        if event.discovery_latency_seconds is None:
            event.discovery_latency_seconds = compute_discovery_latency_seconds(
                event.published_at, event.discovered_at
            )
        d = event.to_dict()
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO intelligence_events (
                    id, title, summary, category, subcategory, project, token, blockchain,
                    source, source_url, source_type, published_at, discovered_at,
                    confidence, importance, sentiment, entities, tags, status, created_at,
                    discovery_latency_seconds, related_sources, fingerprint, cluster_id,
                    source_tier, why_it_matters, what_happened, airdrop_signal_status,
                    is_demo, raw_text
                ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    summary=excluded.summary,
                    category=excluded.category,
                    subcategory=excluded.subcategory,
                    project=excluded.project,
                    token=excluded.token,
                    blockchain=excluded.blockchain,
                    source=excluded.source,
                    source_url=excluded.source_url,
                    source_type=excluded.source_type,
                    published_at=excluded.published_at,
                    discovered_at=excluded.discovered_at,
                    confidence=excluded.confidence,
                    importance=excluded.importance,
                    sentiment=excluded.sentiment,
                    entities=excluded.entities,
                    tags=excluded.tags,
                    status=excluded.status,
                    discovery_latency_seconds=excluded.discovery_latency_seconds,
                    related_sources=excluded.related_sources,
                    fingerprint=excluded.fingerprint,
                    cluster_id=excluded.cluster_id,
                    source_tier=excluded.source_tier,
                    why_it_matters=excluded.why_it_matters,
                    what_happened=excluded.what_happened,
                    airdrop_signal_status=excluded.airdrop_signal_status,
                    is_demo=excluded.is_demo,
                    raw_text=excluded.raw_text
                """,
                (
                    d["id"], d["title"], d["summary"], d["category"], d["subcategory"],
                    d["project"], d["token"], d["blockchain"], d["source"], d["source_url"],
                    d["source_type"], d["published_at"], d["discovered_at"], d["confidence"],
                    d["importance"], d["sentiment"], d["entities_json"], d["tags_json"],
                    d["status"], d["created_at"], d["discovery_latency_seconds"],
                    d["related_sources_json"], d["fingerprint"], d["cluster_id"],
                    d["source_tier"], d["why_it_matters"], d["what_happened"],
                    d["airdrop_signal_status"], 1 if d["is_demo"] else 0, d["raw_text"],
                ),
            )
        return event.id

    def get_event(self, event_id: str) -> Optional[IntelligenceEvent]:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM intelligence_events WHERE id=? LIMIT 1", (event_id,)
            ).fetchone()
            return IntelligenceEvent.from_row(dict(row)) if row else None

    def list_events(
        self,
        *,
        category: Optional[str] = None,
        status: Optional[str] = None,
        include_demo: bool = True,
        include_live: bool = True,
        limit: int = 50,
        min_importance: int = 0,
    ) -> list[IntelligenceEvent]:
        clauses = ["1=1"]
        params: list[Any] = []
        if category:
            clauses.append("category=?")
            params.append(category)
        if status:
            clauses.append("status=?")
            params.append(status)
        else:
            clauses.append("status NOT IN ('IGNORED','ARCHIVED')")
        if include_demo and not include_live:
            clauses.append("is_demo=1")
        elif include_live and not include_demo:
            clauses.append("is_demo=0")
        elif not include_demo and not include_live:
            return []
        clauses.append("importance>=?")
        params.append(int(min_importance))
        params.append(int(limit))
        sql = (
            f"SELECT * FROM intelligence_events WHERE {' AND '.join(clauses)} "
            "ORDER BY importance DESC, COALESCE(published_at, discovered_at) DESC LIMIT ?"
        )
        with connect(self.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
            return [IntelligenceEvent.from_row(dict(r)) for r in rows]

    def existing_fingerprints(self) -> set[str]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT fingerprint FROM intelligence_events WHERE fingerprint!=''"
            ).fetchall()
            return {r["fingerprint"] for r in rows}

    def set_event_status(self, event_id: str, status: str) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                "UPDATE intelligence_events SET status=? WHERE id=?",
                (status, event_id),
            )

    def count_events(self, *, is_demo: Optional[bool] = None) -> int:
        with connect(self.db_path) as conn:
            if is_demo is None:
                row = conn.execute("SELECT COUNT(*) AS c FROM intelligence_events").fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) AS c FROM intelligence_events WHERE is_demo=?",
                    (1 if is_demo else 0,),
                ).fetchone()
            return int(row["c"] if row else 0)

    # --- funding ---
    def add_funding(self, rec: FundingRecord, event_id: str = "") -> str:
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO funding_rounds (
                    id, project, amount, currency, round_type, announced_at,
                    source_url, confidence, notes, is_demo, investors_json, event_id, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    rec.id, rec.project, rec.amount or NOT_DISCLOSED, rec.currency,
                    rec.round_type or UNKNOWN, rec.announced_at, rec.source_url,
                    rec.confidence, rec.notes, 1 if rec.is_demo else 0,
                    json.dumps(rec.investors), event_id, rec.created_at,
                ),
            )
        return rec.id

    def list_funding(self, limit: int = 50) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM funding_rounds ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    # --- candidates (do not auto-verify) ---
    def add_candidate(self, cand: CandidateProject) -> str:
        # Force DISCOVERED on create — never auto VERIFIED
        if cand.status not in {s.value for s in CandidateProjectStatus}:
            cand.status = CandidateProjectStatus.DISCOVERED.value
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO intelligence_candidates (
                    id, name, status, blockchain, website, notes, source_event_id,
                    linked_project_id, is_demo, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    cand.id, cand.name, cand.status, cand.blockchain, cand.website,
                    cand.notes, cand.source_event_id, None, 1 if cand.is_demo else 0,
                    cand.created_at, cand.updated_at,
                ),
            )
        return cand.id

    def list_candidates(self, limit: int = 50) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM intelligence_candidates ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def advance_candidate(self, cand_id: str, new_status: str) -> None:
        """Manual review transitions only — caller must not skip REVIEW for auto-verify."""
        allowed = {s.value for s in CandidateProjectStatus}
        if new_status not in allowed:
            raise ValueError(f"Invalid candidate status: {new_status}")
        with connect(self.db_path) as conn:
            conn.execute(
                "UPDATE intelligence_candidates SET status=?, updated_at=? WHERE id=?",
                (new_status, utc_now(), cand_id),
            )

    # --- narratives ---
    def upsert_narrative(
        self,
        *,
        slug: str,
        title: str,
        summary: str = "",
        tags: Optional[list[str]] = None,
        is_demo: bool = False,
        heat: int = 0,
    ) -> str:
        now = utc_now()
        nid = str(uuid4())
        with connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM narratives WHERE slug=? LIMIT 1", (slug,)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE narratives SET title=?, summary=?, tags=?, is_demo=?, heat=?, updated_at=?
                       WHERE slug=?""",
                    (
                        title, summary, json.dumps(tags or []), 1 if is_demo else 0,
                        int(heat), now, slug,
                    ),
                )
                return str(existing["id"])
            conn.execute(
                """INSERT INTO narratives (id, slug, title, summary, tags, is_demo, heat, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    nid, slug, title, summary, json.dumps(tags or []),
                    1 if is_demo else 0, int(heat), now, now,
                ),
            )
        return nid

    def list_narratives(self, limit: int = 20) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM narratives ORDER BY heat DESC, updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                try:
                    d["tags"] = json.loads(d.get("tags") or "[]")
                except json.JSONDecodeError:
                    d["tags"] = []
                out.append(d)
            return out

    # --- intelligence watchlist (separate from market watchlist; stub-friendly) ---
    def add_watch(self, ref_type: str, ref_id: str, user_id: Optional[int] = None, notes: str = "") -> int:
        with connect(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO intelligence_watchlist (user_id, ref_type, ref_id, notes, created_at)
                   VALUES (?,?,?,?,?)""",
                (user_id, ref_type, str(ref_id), notes, utc_now()),
            )
            return int(cur.lastrowid)

    def list_watch(self, user_id: Optional[int] = None, limit: int = 50) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            if user_id is None:
                rows = conn.execute(
                    "SELECT * FROM intelligence_watchlist ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM intelligence_watchlist WHERE user_id IS ? OR user_id=?
                       ORDER BY created_at DESC LIMIT ?""",
                    (None, user_id, limit),
                ).fetchall()
            return [dict(r) for r in rows]

    # --- ingestion runs ---
    def start_run(self, sources: list[str]) -> str:
        rid = str(uuid4())
        with connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO ingestion_runs (id, started_at, status, sources_json)
                   VALUES (?,?,?,?)""",
                (rid, utc_now(), "running", json.dumps(sources)),
            )
        return rid

    def finish_run(
        self,
        run_id: str,
        *,
        status: str = "ok",
        docs_ingested: int = 0,
        docs_stored: int = 0,
        docs_deduped: int = 0,
        error: str = "",
        meta: Optional[dict] = None,
    ) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                """UPDATE ingestion_runs SET finished_at=?, status=?, docs_ingested=?,
                   docs_stored=?, docs_deduped=?, error=?, meta_json=? WHERE id=?""",
                (
                    utc_now(), status, docs_ingested, docs_stored, docs_deduped,
                    error, json.dumps(meta or {}), run_id,
                ),
            )

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM ingestion_runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def upsert_source_row(self, key: str, name: str, tier: int, source_type: str, **kwargs: Any) -> None:
        now = utc_now()
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO intelligence_sources (
                    key, name, tier, source_type, feed_url, homepage, enabled,
                    min_interval_seconds, notes, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(key) DO UPDATE SET
                    name=excluded.name, tier=excluded.tier, source_type=excluded.source_type,
                    feed_url=excluded.feed_url, homepage=excluded.homepage,
                    enabled=excluded.enabled, min_interval_seconds=excluded.min_interval_seconds,
                    notes=excluded.notes, updated_at=excluded.updated_at
                """,
                (
                    key, name, int(tier), source_type,
                    kwargs.get("feed_url", ""), kwargs.get("homepage", ""),
                    1 if kwargs.get("enabled", True) else 0,
                    int(kwargs.get("min_interval_seconds", 900)),
                    kwargs.get("notes", ""), now, now,
                ),
            )
