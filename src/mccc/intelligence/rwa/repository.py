"""RWARepository — SQLite locally; interface ready for durable production DB.

Relationships: Project → RWA Profile → Events → Funding → Sources → Watchlist → Research.
Does not duplicate the projects table; links via project_id when present.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from mccc.db import connect, utc_now
from mccc.intelligence.rwa.schema import RWAProfile, TokenizedAssetValue
from mccc.intelligence.rwa.taxonomy import VerificationStatus
from mccc.intelligence.schema import UNKNOWN

# Asset value older than this is marked stale in reads
STALE_AFTER_DAYS = 30

RWA_SCHEMA = """
CREATE TABLE IF NOT EXISTS rwa_profiles (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    ticker TEXT DEFAULT 'Unknown',
    description TEXT DEFAULT '',
    rwa_category TEXT DEFAULT '',
    asset_type TEXT DEFAULT 'Unknown',
    blockchain TEXT DEFAULT 'Unknown',
    website_url TEXT DEFAULT '',
    docs_url TEXT DEFAULT '',
    launch_status TEXT DEFAULT 'Unknown',
    token_status TEXT DEFAULT 'Unknown',
    tokenization_model TEXT DEFAULT 'Unknown',
    jurisdiction TEXT DEFAULT 'Unknown',
    regulatory_status TEXT DEFAULT 'Not disclosed',
    custody_info TEXT DEFAULT 'Not disclosed',
    issuer_info TEXT DEFAULT 'Not disclosed',
    collateral_info TEXT DEFAULT 'Not disclosed',
    funding_notes TEXT DEFAULT 'Not disclosed',
    funding_round_id TEXT DEFAULT '',
    tokenized_asset_value_json TEXT DEFAULT '',
    confidence TEXT DEFAULT 'UNCONFIRMED',
    verification_status TEXT NOT NULL DEFAULT 'DISCOVERED',
    discovered_at TEXT NOT NULL,
    last_checked_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    project_id INTEGER,
    source_event_id TEXT DEFAULT '',
    is_demo INTEGER NOT NULL DEFAULT 0,
    tags_json TEXT DEFAULT '[]',
    disclosures_json TEXT DEFAULT '[]',
    provenance_json TEXT DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_rwa_cat ON rwa_profiles(rwa_category);
CREATE INDEX IF NOT EXISTS idx_rwa_chain ON rwa_profiles(blockchain);
CREATE INDEX IF NOT EXISTS idx_rwa_verif ON rwa_profiles(verification_status);
CREATE INDEX IF NOT EXISTS idx_rwa_demo ON rwa_profiles(is_demo);
CREATE INDEX IF NOT EXISTS idx_rwa_project ON rwa_profiles(project_id);
CREATE INDEX IF NOT EXISTS idx_rwa_name ON rwa_profiles(project_name);

CREATE TABLE IF NOT EXISTS rwa_profile_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    rwa_event_type TEXT DEFAULT 'OTHER',
    created_at TEXT NOT NULL,
    UNIQUE(profile_id, event_id)
);
CREATE INDEX IF NOT EXISTS idx_rwa_pe_profile ON rwa_profile_events(profile_id);
CREATE INDEX IF NOT EXISTS idx_rwa_pe_event ON rwa_profile_events(event_id);

CREATE TABLE IF NOT EXISTS rwa_watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ref_type TEXT NOT NULL DEFAULT 'project',
    ref_id TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rwa_watch_user ON rwa_watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_rwa_watch_ref ON rwa_watchlist(ref_type, ref_id);
"""


def _parse_iso(iso: str) -> Optional[datetime]:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def mark_stale(value: TokenizedAssetValue, *, now: Optional[datetime] = None) -> TokenizedAssetValue:
    """Flag asset values whose measurement timestamp is older than STALE_AFTER_DAYS."""
    now = now or datetime.now(timezone.utc)
    measured = _parse_iso(value.measured_at)
    if measured is None:
        if value.value_type != "unavailable" and value.amount not in ("", UNKNOWN, "Unknown"):
            value.is_stale = True
        return value
    value.is_stale = measured < (now - timedelta(days=STALE_AFTER_DAYS))
    return value


class RWARepository:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path

    def ensure_schema(self) -> None:
        with connect(self.db_path) as conn:
            conn.executescript(RWA_SCHEMA)

    def upsert_profile(self, profile: RWAProfile) -> str:
        d = profile.to_dict()
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO rwa_profiles (
                    id, project_name, ticker, description, rwa_category, asset_type,
                    blockchain, website_url, docs_url, launch_status, token_status,
                    tokenization_model, jurisdiction, regulatory_status, custody_info,
                    issuer_info, collateral_info, funding_notes, funding_round_id,
                    tokenized_asset_value_json, confidence, verification_status,
                    discovered_at, last_checked_at, created_at, updated_at,
                    project_id, source_event_id, is_demo, tags_json, disclosures_json,
                    provenance_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    project_name=excluded.project_name,
                    ticker=excluded.ticker,
                    description=excluded.description,
                    rwa_category=excluded.rwa_category,
                    asset_type=excluded.asset_type,
                    blockchain=excluded.blockchain,
                    website_url=excluded.website_url,
                    docs_url=excluded.docs_url,
                    launch_status=excluded.launch_status,
                    token_status=excluded.token_status,
                    tokenization_model=excluded.tokenization_model,
                    jurisdiction=excluded.jurisdiction,
                    regulatory_status=excluded.regulatory_status,
                    custody_info=excluded.custody_info,
                    issuer_info=excluded.issuer_info,
                    collateral_info=excluded.collateral_info,
                    funding_notes=excluded.funding_notes,
                    funding_round_id=excluded.funding_round_id,
                    tokenized_asset_value_json=excluded.tokenized_asset_value_json,
                    confidence=excluded.confidence,
                    verification_status=excluded.verification_status,
                    discovered_at=excluded.discovered_at,
                    last_checked_at=excluded.last_checked_at,
                    updated_at=excluded.updated_at,
                    project_id=excluded.project_id,
                    source_event_id=excluded.source_event_id,
                    is_demo=excluded.is_demo,
                    tags_json=excluded.tags_json,
                    disclosures_json=excluded.disclosures_json,
                    provenance_json=excluded.provenance_json
                """,
                (
                    d["id"], d["project_name"], d["ticker"], d["description"],
                    d["rwa_category"], d["asset_type"], d["blockchain"],
                    d["website_url"], d["docs_url"], d["launch_status"],
                    d["token_status"], d["tokenization_model"], d["jurisdiction"],
                    d["regulatory_status"], d["custody_info"], d["issuer_info"],
                    d["collateral_info"], d["funding_notes"], d["funding_round_id"],
                    d["tokenized_asset_value_json"], d["confidence"],
                    d["verification_status"], d["discovered_at"], d["last_checked_at"],
                    d["created_at"], d["updated_at"], d["project_id"],
                    d["source_event_id"], 1 if d["is_demo"] else 0,
                    d["tags_json"], d["disclosures_json"], d["provenance_json"],
                ),
            )
        return profile.id

    def get_profile(self, profile_id: str) -> Optional[RWAProfile]:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM rwa_profiles WHERE id=? LIMIT 1", (profile_id,)
            ).fetchone()
            if not row:
                return None
            return self._hydrate(dict(row))

    def find_by_name(self, project_name: str) -> Optional[RWAProfile]:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM rwa_profiles WHERE lower(project_name)=lower(?) LIMIT 1",
                (project_name.strip(),),
            ).fetchone()
            if not row:
                return None
            return self._hydrate(dict(row))

    def _hydrate(self, row: dict[str, Any]) -> RWAProfile:
        row = dict(row)
        row["tags"] = row.get("tags_json") or "[]"
        row["disclosures"] = row.get("disclosures_json") or "[]"
        row["provenance"] = row.get("provenance_json") or "[]"
        profile = RWAProfile.from_row(row)
        av = mark_stale(profile.asset_value())
        profile.set_asset_value(av)
        return profile

    def list_profiles(
        self,
        *,
        category: Optional[str] = None,
        blockchain: Optional[str] = None,
        verification_status: Optional[str] = None,
        confidence: Optional[str] = None,
        include_demo: bool = True,
        include_live: bool = True,
        q: Optional[str] = None,
        limit: int = 100,
    ) -> list[RWAProfile]:
        clauses = ["1=1"]
        params: list[Any] = []
        if category:
            clauses.append("rwa_category=?")
            params.append(category)
        if blockchain:
            clauses.append("lower(blockchain)=lower(?)")
            params.append(blockchain)
        if verification_status:
            clauses.append("verification_status=?")
            params.append(verification_status)
        if confidence:
            clauses.append("confidence=?")
            params.append(confidence)
        if include_demo and not include_live:
            clauses.append("is_demo=1")
        elif include_live and not include_demo:
            clauses.append("is_demo=0")
        elif not include_demo and not include_live:
            return []
        if q:
            needle = f"%{(q or '').strip().lower()}%"
            clauses.append(
                "(lower(project_name) LIKE ? OR lower(ticker) LIKE ? OR lower(description) LIKE ?"
                " OR lower(rwa_category) LIKE ? OR lower(blockchain) LIKE ? OR lower(tags_json) LIKE ?)"
            )
            params.extend([needle] * 6)
        params.append(int(limit))
        sql = (
            f"SELECT * FROM rwa_profiles WHERE {' AND '.join(clauses)} "
            "ORDER BY updated_at DESC LIMIT ?"
        )
        with connect(self.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._hydrate(dict(r)) for r in rows]

    def count_profiles(self, *, is_demo: Optional[bool] = None) -> int:
        with connect(self.db_path) as conn:
            if is_demo is None:
                row = conn.execute("SELECT COUNT(*) AS c FROM rwa_profiles").fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) AS c FROM rwa_profiles WHERE is_demo=?",
                    (1 if is_demo else 0,),
                ).fetchone()
            return int(row["c"] if row else 0)

    def set_verification(self, profile_id: str, status: str) -> None:
        allowed = {s.value for s in VerificationStatus}
        if status not in allowed:
            raise ValueError(f"Invalid verification status: {status}")
        with connect(self.db_path) as conn:
            conn.execute(
                "UPDATE rwa_profiles SET verification_status=?, updated_at=?, last_checked_at=? WHERE id=?",
                (status, utc_now(), utc_now(), profile_id),
            )

    def link_event(self, profile_id: str, event_id: str, rwa_event_type: str = "OTHER") -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR IGNORE INTO rwa_profile_events
                   (profile_id, event_id, rwa_event_type, created_at)
                   VALUES (?,?,?,?)""",
                (profile_id, event_id, rwa_event_type, utc_now()),
            )

    def list_linked_events(self, profile_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT * FROM rwa_profile_events WHERE profile_id=?
                   ORDER BY created_at DESC LIMIT ?""",
                (profile_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def link_project(self, profile_id: str, project_id: int) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                "UPDATE rwa_profiles SET project_id=?, updated_at=? WHERE id=?",
                (project_id, utc_now(), profile_id),
            )

    def link_funding(self, profile_id: str, funding_round_id: str) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                "UPDATE rwa_profiles SET funding_round_id=?, updated_at=? WHERE id=?",
                (funding_round_id, utc_now(), profile_id),
            )

    # --- RWA watchlist ---
    def add_watch(
        self,
        ref_type: str,
        ref_id: str,
        user_id: Optional[int] = None,
        notes: str = "",
    ) -> int:
        allowed = {"project", "category", "chain", "narrative", "profile"}
        rt = (ref_type or "project").strip().lower()
        if rt not in allowed:
            rt = "project"
        with connect(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO rwa_watchlist (user_id, ref_type, ref_id, notes, created_at)
                   VALUES (?,?,?,?,?)""",
                (user_id, rt, str(ref_id), notes, utc_now()),
            )
            return int(cur.lastrowid)

    def list_watch(self, user_id: Optional[int] = None, limit: int = 50) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            if user_id is None:
                rows = conn.execute(
                    "SELECT * FROM rwa_watchlist ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM rwa_watchlist WHERE user_id IS ? OR user_id=?
                       ORDER BY created_at DESC LIMIT ?""",
                    (None, user_id, limit),
                ).fetchall()
            return [dict(r) for r in rows]

    def remove_watch(self, watch_id: int) -> None:
        with connect(self.db_path) as conn:
            conn.execute("DELETE FROM rwa_watchlist WHERE id=?", (watch_id,))

    def analytics_summary(self, *, include_demo: bool = True) -> dict[str, Any]:
        """Dashboard analytics from stored profiles only — no fabricated TVL."""
        profiles = self.list_profiles(include_demo=include_demo, include_live=True, limit=500)
        by_cat: dict[str, int] = {}
        by_chain: dict[str, int] = {}
        by_verif: dict[str, int] = {}
        demo_n = 0
        live_n = 0
        with_value = 0
        stale_n = 0
        for p in profiles:
            by_cat[p.rwa_category or "unknown"] = by_cat.get(p.rwa_category or "unknown", 0) + 1
            by_chain[p.blockchain or UNKNOWN] = by_chain.get(p.blockchain or UNKNOWN, 0) + 1
            by_verif[p.verification_status] = by_verif.get(p.verification_status, 0) + 1
            if p.is_demo:
                demo_n += 1
            else:
                live_n += 1
            av = p.asset_value()
            if av.value_type != "unavailable" and av.amount not in (UNKNOWN, "", "Unknown"):
                with_value += 1
            if av.is_stale:
                stale_n += 1
        return {
            "total": len(profiles),
            "demo": demo_n,
            "live": live_n,
            "by_category": by_cat,
            "by_chain": by_chain,
            "by_verification": by_verif,
            "with_asset_value": with_value,
            "stale_asset_values": stale_n,
            "data_mode": "DEMO" if demo_n and not live_n else ("MIXED" if demo_n and live_n else ("LIVE" if live_n else "EMPTY")),
        }

    def observed_narratives(self) -> list[dict[str, Any]]:
        """Narratives derived only from stored RWA categories (observed data)."""
        summary = self.analytics_summary(include_demo=True)
        out = []
        for cat, count in sorted(summary["by_category"].items(), key=lambda x: -x[1]):
            if not cat or cat == "unknown":
                continue
            out.append(
                {
                    "slug": f"rwa-{cat.replace('_', '-')}",
                    "title": f"RWA · {cat.replace('_', ' ').title()}",
                    "heat": int(count),
                    "summary": f"Observed from {count} stored RWA profile(s) — not invented.",
                    "is_demo": summary["demo"] > 0 and summary["live"] == 0,
                }
            )
        return out
