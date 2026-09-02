"""SQLite persistence for MCCC — projects, airdrops, wallets, partners, usage stats."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Iterable, Optional

from mccc.paths import DB_PATH, ensure_dirs

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    chain TEXT DEFAULT '',
    status TEXT DEFAULT 'researching',
    notes TEXT DEFAULT '',
    priority INTEGER DEFAULT 3,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS airdrops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    chain TEXT DEFAULT '',
    status TEXT DEFAULT 'watching',
    eligibility_notes TEXT DEFAULT '',
    estimated_value TEXT DEFAULT 'DEMO / unknown',
    deadline TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    address TEXT NOT NULL,
    chain TEXT DEFAULT 'ethereum',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    page_key TEXT DEFAULT '',
    meta TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feature_flags (
    key TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS research_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    official_url TEXT NOT NULL,
    referral_url TEXT DEFAULT '',
    description TEXT DEFAULT '',
    features TEXT DEFAULT '',
    networks TEXT DEFAULT '',
    logo_url TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Active',
    is_referral INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_link_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_link_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    clicked_at TEXT NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    ensure_dirs()
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        _seed_feature_flags(conn)
        _seed_airdrops_if_empty(conn)
        _seed_projects_if_empty(conn)
    # Seed partner directory only when empty (outside connect so partners.py uses its own txn)
    from mccc.partners import seed_demo_partners

    seed_demo_partners(db_path)


def _seed_feature_flags(conn: sqlite3.Connection) -> None:
    defaults = [
        ("pro_advanced_analytics", 0, "PRO: multi-series analytics & export"),
        ("pro_wallet_alerts", 0, "PRO: watchlist alerts mock"),
        ("pro_ai_deep_research", 0, "PRO: extended research checklists"),
        ("pro_portfolio_sync", 0, "PRO: portfolio sync architecture mock"),
    ]
    for key, enabled, desc in defaults:
        conn.execute(
            "INSERT OR IGNORE INTO feature_flags (key, enabled, description) VALUES (?, ?, ?)",
            (key, enabled, desc),
        )


def _seed_projects_if_empty(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()
    if row and row["c"] > 0:
        return
    now = utc_now()
    demos = [
        ("DEMO: Layer-2 Research Brief", "ethereum", "researching", "EXAMPLE notes — compare fees, TVL, bridge risk.", 2),
        ("DEMO: DeFi Protocol Diligence", "multi", "watching", "EXAMPLE — read docs, audit status, token unlocks.", 3),
        ("DEMO: NFT Market Structure", "ethereum", "archived", "EXAMPLE case closed — education only.", 5),
    ]
    for name, chain, status, notes, priority in demos:
        conn.execute(
            """INSERT INTO projects (name, chain, status, notes, priority, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, chain, status, notes, priority, now, now),
        )


def _seed_airdrops_if_empty(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS c FROM airdrops").fetchone()
    if row and row["c"] > 0:
        return
    now = utc_now()
    demos = [
        ("DEMO Protocol Alpha", "ethereum", "watching", "EXAMPLE: testnet txs, Discord role — not live eligibility.", "DEMO / unknown", ""),
        ("DEMO Chain Beta Points", "solana", "eligible", "EXAMPLE: points program notes for research practice.", "DEMO estimate only", "TBD"),
        ("DEMO Governance Gamma", "arbitrum", "claimed", "EXAMPLE claimed entry — educational tracker.", "DEMO", "2024-01-01"),
    ]
    for name, chain, status, notes, value, deadline in demos:
        conn.execute(
            """INSERT INTO airdrops (project_name, chain, status, eligibility_notes, estimated_value, deadline, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, chain, status, notes, value, deadline, now, now),
        )


# --- Projects ---

def list_projects(db_path: Optional[Path] = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY priority ASC, updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def add_project(
    name: str,
    chain: str = "",
    status: str = "researching",
    notes: str = "",
    priority: int = 3,
    db_path: Optional[Path] = None,
) -> int:
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO projects (name, chain, status, notes, priority, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name.strip(), chain.strip(), status, notes, priority, now, now),
        )
        return int(cur.lastrowid)


def update_project(project_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    allowed = {"name", "chain", "status", "notes", "priority"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = utc_now()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [project_id]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE projects SET {cols} WHERE id=?", vals)


def delete_project(project_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))


# --- Airdrops ---

def list_airdrops(db_path: Optional[Path] = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM airdrops ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def add_airdrop(
    project_name: str,
    chain: str = "",
    status: str = "watching",
    eligibility_notes: str = "",
    estimated_value: str = "DEMO / unknown",
    deadline: str = "",
    db_path: Optional[Path] = None,
) -> int:
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO airdrops (project_name, chain, status, eligibility_notes, estimated_value, deadline, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_name.strip(),
                chain.strip(),
                status,
                eligibility_notes,
                estimated_value,
                deadline,
                now,
                now,
            ),
        )
        return int(cur.lastrowid)


def update_airdrop(airdrop_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    allowed = {"project_name", "chain", "status", "eligibility_notes", "estimated_value", "deadline"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = utc_now()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [airdrop_id]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE airdrops SET {cols} WHERE id=?", vals)


def delete_airdrop(airdrop_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM airdrops WHERE id=?", (airdrop_id,))


# --- Wallets (public addresses only) ---

def list_wallets(db_path: Optional[Path] = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM wallets ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def add_wallet(
    label: str,
    address: str,
    chain: str = "ethereum",
    notes: str = "",
    db_path: Optional[Path] = None,
) -> int:
    addr = address.strip()
    if not addr or " " in addr:
        raise ValueError("Address must be a non-empty public address string")
    # Refuse anything that looks like a private key / seed
    lowered = addr.lower()
    if any(x in lowered for x in ("private", "seed", "mnemonic", "0x" + "0" * 60)):
        if "private" in lowered or "seed" in lowered or "mnemonic" in lowered:
            raise ValueError("Private keys and seed phrases are not allowed")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO wallets (label, address, chain, notes, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (label.strip(), addr, chain.strip(), notes, now),
        )
        return int(cur.lastrowid)


def delete_wallet(wallet_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM wallets WHERE id=?", (wallet_id,))


# --- Usage analytics ---

def log_event(event_type: str, page_key: str = "", meta: str = "", db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO usage_events (event_type, page_key, meta, created_at) VALUES (?, ?, ?, ?)",
            (event_type, page_key, meta, utc_now()),
        )


def usage_summary(db_path: Optional[Path] = None) -> dict[str, Any]:
    with connect(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM usage_events").fetchone()["c"]
        by_page = conn.execute(
            """SELECT page_key, COUNT(*) AS c FROM usage_events
               WHERE event_type='page_view' AND page_key != ''
               GROUP BY page_key ORDER BY c DESC"""
        ).fetchall()
        by_type = conn.execute(
            "SELECT event_type, COUNT(*) AS c FROM usage_events GROUP BY event_type ORDER BY c DESC"
        ).fetchall()
        recent = conn.execute(
            "SELECT * FROM usage_events ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    return {
        "total_events": total,
        "by_page": [dict(r) for r in by_page],
        "by_type": [dict(r) for r in by_type],
        "recent": [dict(r) for r in recent],
    }


# --- Feature flags ---

def get_feature_flags(db_path: Optional[Path] = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM feature_flags ORDER BY key").fetchall()
        return [dict(r) for r in rows]


def set_feature_flag(key: str, enabled: bool, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE feature_flags SET enabled=? WHERE key=?",
            (1 if enabled else 0, key),
        )


def is_feature_enabled(key: str, db_path: Optional[Path] = None) -> bool:
    import os

    if os.environ.get("MCCC_PRO_UNLOCK", "0") == "1":
        return True
    with connect(db_path) as conn:
        row = conn.execute("SELECT enabled FROM feature_flags WHERE key=?", (key,)).fetchone()
        return bool(row and row["enabled"])


# --- Research notes ---

def list_notes(db_path: Optional[Path] = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM research_notes ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def add_note(title: str, body: str = "", tags: str = "", db_path: Optional[Path] = None) -> int:
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO research_notes (title, body, tags, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (title.strip(), body, tags, now, now),
        )
        return int(cur.lastrowid)
