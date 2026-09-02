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
    description TEXT DEFAULT '',
    category TEXT DEFAULT '',
    risk_rating TEXT DEFAULT '',
    funding TEXT DEFAULT '',
    investors TEXT DEFAULT '',
    token TEXT DEFAULT '',
    tge TEXT DEFAULT '',
    website TEXT DEFAULT '',
    docs TEXT DEFAULT '',
    social_links TEXT DEFAULT '',
    tasks TEXT DEFAULT '',
    wallet TEXT DEFAULT '',
    last_checked TEXT DEFAULT '',
    next_action TEXT DEFAULT '',
    stage TEXT DEFAULT 'Researching',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS airdrops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    chain TEXT DEFAULT '',
    status TEXT DEFAULT 'Discovered',
    eligibility_notes TEXT DEFAULT '',
    estimated_value TEXT DEFAULT 'DEMO / unknown',
    deadline TEXT DEFAULT '',
    category TEXT DEFAULT '',
    start_date TEXT DEFAULT '',
    end_date TEXT DEFAULT '',
    tge_date TEXT DEFAULT '',
    token TEXT DEFAULT '',
    eligibility TEXT DEFAULT '',
    points TEXT DEFAULT '',
    rank TEXT DEFAULT '',
    wallet_used TEXT DEFAULT '',
    official_website TEXT DEFAULT '',
    docs_url TEXT DEFAULT '',
    discord TEXT DEFAULT '',
    twitter TEXT DEFAULT '',
    telegram TEXT DEFAULT '',
    claim_page TEXT DEFAULT '',
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

CREATE TABLE IF NOT EXISTS analytics_events (
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
    clicked_at TEXT NOT NULL,
    source_page TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    experience_level TEXT DEFAULT '',
    onboarding_goals TEXT DEFAULT '',
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY,
    theme TEXT DEFAULT 'dark',
    notify_prefs TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS portfolio_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    symbol TEXT NOT NULL,
    name TEXT DEFAULT '',
    quantity REAL NOT NULL DEFAULT 0,
    purchase_price REAL NOT NULL DEFAULT 0,
    purchase_date TEXT DEFAULT '',
    network TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio_assets(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio_assets(symbol);

CREATE TABLE IF NOT EXISTS watchlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_type TEXT NOT NULL DEFAULT 'token',
    symbol_or_ref TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist_items(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_type ON watchlist_items(item_type);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    watchlist_id INTEGER,
    alert_type TEXT NOT NULL DEFAULT 'price',
    threshold REAL,
    meta TEXT DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(active);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    category TEXT DEFAULT 'general',
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);

CREATE TABLE IF NOT EXISTS airdrop_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airdrop_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (airdrop_id) REFERENCES airdrops(id)
);
CREATE INDEX IF NOT EXISTS idx_airdrop_tasks_aid ON airdrop_tasks(airdrop_id);

CREATE TABLE IF NOT EXISTS education_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    lesson_key TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    quiz_score REAL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_education_user ON education_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_education_lesson ON education_progress(lesson_key);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tier TEXT NOT NULL DEFAULT 'free',
    status TEXT DEFAULT 'active',
    provider TEXT DEFAULT 'coming_soon',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);

CREATE TABLE IF NOT EXISTS ai_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    kind TEXT NOT NULL DEFAULT 'chat',
    tokens_est INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_usage_user ON ai_usage(user_id);

CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_page ON analytics_events(page_key);
"""



PROJECT_STAGES = (
    "Discovered",
    "Researching",
    "Farming",
    "Monitoring",
    "TGE Soon",
    "Completed",
)

AIRDROP_STATUSES = (
    "Discovered",
    "Researching",
    "Farming",
    "Waiting",
    "TGE Soon",
    "Claim Available",
    "Claimed",
    "Completed",
    "Dead",
)

_STATUS_TO_STAGE = {
    "researching": "Researching",
    "watching": "Monitoring",
    "archived": "Completed",
    "discovered": "Discovered",
    "farming": "Farming",
    "monitoring": "Monitoring",
    "tge soon": "TGE Soon",
    "completed": "Completed",
}

_AIRDROP_STATUS_MAP = {
    "watching": "Discovered",
    "eligible": "Claim Available",
    "claimed": "Claimed",
    "researching": "Researching",
    "farming": "Farming",
    "waiting": "Waiting",
    "tge soon": "TGE Soon",
    "claim available": "Claim Available",
    "completed": "Completed",
    "dead": "Dead",
    "discovered": "Discovered",
}


def _ensure_column(conn: sqlite3.Connection, table: str, col: str, typedef: str) -> None:
    """Add column if missing (SQLite ALTER TABLE ADD COLUMN). Safe to call repeatedly."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {r[1] for r in rows}
    if col not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}")


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Extend legacy tables and normalize status/stage values."""
    # projects extended columns
    for col, typedef in [
        ("description", "TEXT DEFAULT ''"),
        ("category", "TEXT DEFAULT ''"),
        ("risk_rating", "TEXT DEFAULT ''"),
        ("funding", "TEXT DEFAULT ''"),
        ("investors", "TEXT DEFAULT ''"),
        ("token", "TEXT DEFAULT ''"),
        ("tge", "TEXT DEFAULT ''"),
        ("website", "TEXT DEFAULT ''"),
        ("docs", "TEXT DEFAULT ''"),
        ("social_links", "TEXT DEFAULT ''"),
        ("tasks", "TEXT DEFAULT ''"),
        ("wallet", "TEXT DEFAULT ''"),
        ("last_checked", "TEXT DEFAULT ''"),
        ("next_action", "TEXT DEFAULT ''"),
        ("stage", "TEXT DEFAULT 'Researching'"),
    ]:
        _ensure_column(conn, "projects", col, typedef)

    # airdrops extended columns
    for col, typedef in [
        ("category", "TEXT DEFAULT ''"),
        ("start_date", "TEXT DEFAULT ''"),
        ("end_date", "TEXT DEFAULT ''"),
        ("tge_date", "TEXT DEFAULT ''"),
        ("token", "TEXT DEFAULT ''"),
        ("eligibility", "TEXT DEFAULT ''"),
        ("points", "TEXT DEFAULT ''"),
        ("rank", "TEXT DEFAULT ''"),
        ("wallet_used", "TEXT DEFAULT ''"),
        ("official_website", "TEXT DEFAULT ''"),
        ("docs_url", "TEXT DEFAULT ''"),
        ("discord", "TEXT DEFAULT ''"),
        ("twitter", "TEXT DEFAULT ''"),
        ("telegram", "TEXT DEFAULT ''"),
        ("claim_page", "TEXT DEFAULT ''"),
    ]:
        _ensure_column(conn, "airdrops", col, typedef)

    _ensure_column(conn, "partner_link_clicks", "source_page", "TEXT DEFAULT ''")

    # Migrate project status → stage when stage empty or still default from old status
    rows = conn.execute("SELECT id, status, stage FROM projects").fetchall()
    for r in rows:
        status = (r["status"] or "").strip()
        stage = (r["stage"] or "").strip()
        mapped = _STATUS_TO_STAGE.get(status.lower())
        # If stage is blank or looks like it was never set while status is legacy
        if mapped and (not stage or stage == "Researching" and status.lower() in ("watching", "archived")):
            conn.execute("UPDATE projects SET stage=? WHERE id=?", (mapped, r["id"]))
        elif mapped and stage not in PROJECT_STAGES:
            conn.execute("UPDATE projects SET stage=? WHERE id=?", (mapped, r["id"]))
        elif stage and stage not in PROJECT_STAGES and mapped:
            conn.execute("UPDATE projects SET stage=? WHERE id=?", (mapped, r["id"]))

    # Migrate airdrop statuses
    arows = conn.execute("SELECT id, status FROM airdrops").fetchall()
    for r in arows:
        status = (r["status"] or "").strip()
        mapped = _AIRDROP_STATUS_MAP.get(status.lower())
        if mapped and status != mapped:
            conn.execute("UPDATE airdrops SET status=? WHERE id=?", (mapped, r["id"]))


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
        _migrate_schema(conn)
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
        ("DEMO: Layer-2 Research Brief", "ethereum", "researching", "Researching", "EXAMPLE notes — compare fees, TVL, bridge risk.", 2),
        ("DEMO: DeFi Protocol Diligence", "multi", "watching", "Monitoring", "EXAMPLE — read docs, audit status, token unlocks.", 3),
        ("DEMO: NFT Market Structure", "ethereum", "archived", "Completed", "EXAMPLE case closed — education only.", 5),
    ]
    for name, chain, status, stage, notes, priority in demos:
        conn.execute(
            """INSERT INTO projects (name, chain, status, stage, notes, priority, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, chain, status, stage, notes, priority, now, now),
        )


def _seed_airdrops_if_empty(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS c FROM airdrops").fetchone()
    if row and row["c"] > 0:
        return
    now = utc_now()
    demos = [
        ("DEMO Protocol Alpha", "ethereum", "Discovered", "EXAMPLE: testnet txs, Discord role — not live eligibility.", "DEMO / unknown", ""),
        ("DEMO Chain Beta Points", "solana", "Claim Available", "EXAMPLE: points program notes for research practice.", "DEMO estimate only", "TBD"),
        ("DEMO Governance Gamma", "arbitrum", "Claimed", "EXAMPLE claimed entry — educational tracker.", "DEMO", "2024-01-01"),
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
    stage: Optional[str] = None,
    db_path: Optional[Path] = None,
    **extra: Any,
) -> int:
    now = utc_now()
    if stage is None:
        stage = _STATUS_TO_STAGE.get((status or "").lower(), "Researching")
    extra_cols = {
        k: v
        for k, v in extra.items()
        if k
        in {
            "description",
            "category",
            "risk_rating",
            "funding",
            "investors",
            "token",
            "tge",
            "website",
            "docs",
            "social_links",
            "tasks",
            "wallet",
            "last_checked",
            "next_action",
        }
    }
    cols = ["name", "chain", "status", "stage", "notes", "priority", "created_at", "updated_at"]
    vals: list[Any] = [name.strip(), chain.strip(), status, stage, notes, priority, now, now]
    for k, v in extra_cols.items():
        cols.append(k)
        vals.append(v)
    placeholders = ", ".join("?" for _ in cols)
    col_sql = ", ".join(cols)
    with connect(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO projects ({col_sql}) VALUES ({placeholders})",
            vals,
        )
        return int(cur.lastrowid)


def update_project(project_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    allowed = {
        "name",
        "chain",
        "status",
        "notes",
        "priority",
        "stage",
        "description",
        "category",
        "risk_rating",
        "funding",
        "investors",
        "token",
        "tge",
        "website",
        "docs",
        "social_links",
        "tasks",
        "wallet",
        "last_checked",
        "next_action",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "status" in updates and "stage" not in updates:
        mapped = _STATUS_TO_STAGE.get(str(updates["status"]).lower())
        if mapped:
            updates["stage"] = mapped
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
    status: str = "Discovered",
    eligibility_notes: str = "",
    estimated_value: str = "DEMO / unknown",
    deadline: str = "",
    db_path: Optional[Path] = None,
    **extra: Any,
) -> int:
    now = utc_now()
    # Accept legacy status aliases
    status = _AIRDROP_STATUS_MAP.get(status.lower(), status) if status else "Discovered"
    extra_allowed = {
        "category",
        "start_date",
        "end_date",
        "tge_date",
        "token",
        "eligibility",
        "points",
        "rank",
        "wallet_used",
        "official_website",
        "docs_url",
        "discord",
        "twitter",
        "telegram",
        "claim_page",
    }
    cols = [
        "project_name",
        "chain",
        "status",
        "eligibility_notes",
        "estimated_value",
        "deadline",
        "created_at",
        "updated_at",
    ]
    vals: list[Any] = [
        project_name.strip(),
        chain.strip(),
        status,
        eligibility_notes,
        estimated_value,
        deadline,
        now,
        now,
    ]
    for k, v in extra.items():
        if k in extra_allowed:
            cols.append(k)
            vals.append(v)
    placeholders = ", ".join("?" for _ in cols)
    with connect(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO airdrops ({', '.join(cols)}) VALUES ({placeholders})",
            vals,
        )
        return int(cur.lastrowid)


def update_airdrop(airdrop_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    allowed = {
        "project_name",
        "chain",
        "status",
        "eligibility_notes",
        "estimated_value",
        "deadline",
        "category",
        "start_date",
        "end_date",
        "tge_date",
        "token",
        "eligibility",
        "points",
        "rank",
        "wallet_used",
        "official_website",
        "docs_url",
        "discord",
        "twitter",
        "telegram",
        "claim_page",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "status" in updates and updates["status"]:
        s = str(updates["status"])
        updates["status"] = _AIRDROP_STATUS_MAP.get(s.lower(), s)
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


def log_analytics_event(
    event_type: str,
    page_key: str = "",
    meta: str = "",
    db_path: Optional[Path] = None,
) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO analytics_events (event_type, page_key, meta, created_at) VALUES (?, ?, ?, ?)",
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
