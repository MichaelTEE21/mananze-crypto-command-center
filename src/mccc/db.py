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
    stage TEXT DEFAULT 'RESEARCHING',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS airdrops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    chain TEXT DEFAULT '',
    status TEXT DEFAULT 'DISCOVERED',
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
    project_id INTEGER,
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

CREATE TABLE IF NOT EXISTS exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'CEX',
    official_url TEXT NOT NULL DEFAULT '',
    referral_url TEXT DEFAULT '',
    docs_url TEXT DEFAULT '',
    chains TEXT DEFAULT '',
    assets TEXT DEFAULT '',
    region TEXT DEFAULT '',
    difficulty TEXT DEFAULT '',
    security_info TEXT DEFAULT '',
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_exchanges_type ON exchanges(type);
CREATE INDEX IF NOT EXISTS idx_exchanges_status ON exchanges(status);

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    resource_type TEXT DEFAULT '',
    project_id INTEGER,
    description TEXT DEFAULT '',
    is_official INTEGER NOT NULL DEFAULT 0,
    click_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_resources_project ON resources(project_id);
CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(resource_type);

CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    published INTEGER NOT NULL DEFAULT 0,
    expires_at TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_announcements_published ON announcements(published);

CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,
    item_ref TEXT NOT NULL,
    notes TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    priority INTEGER DEFAULT 3,
    favourite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bookmarks_type ON bookmarks(item_type);
CREATE INDEX IF NOT EXISTS idx_bookmarks_fav ON bookmarks(favourite);

CREATE TABLE IF NOT EXISTS research_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'note',
    body TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_research_events_project ON research_events(project_id);

CREATE TABLE IF NOT EXISTS project_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_project_tags_project ON project_tags(project_id);
CREATE INDEX IF NOT EXISTS idx_project_tags_tag ON project_tags(tag);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type);
CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'important',
    event_date TEXT NOT NULL,
    end_date TEXT DEFAULT '',
    entity_type TEXT DEFAULT '',
    entity_ref TEXT DEFAULT '',
    project_id INTEGER,
    airdrop_id INTEGER,
    description TEXT DEFAULT '',
    source TEXT DEFAULT '',
    data_quality TEXT DEFAULT 'UNKNOWN',
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_calendar_events_date ON calendar_events(event_date);
CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON calendar_events(event_type);

CREATE INDEX IF NOT EXISTS idx_analytics_events_page ON analytics_events(page_key);
"""



PROJECT_STAGES = (
    "DISCOVERED",
    "RESEARCHING",
    "FARMING",
    "WATCHLIST",
    "WAITING FOR TGE",
    "COMPLETED",
    "ARCHIVED",
)

AIRDROP_STATUSES = (
    "DISCOVERED",
    "RESEARCHING",
    "ACTIVE",
    "COMPLETED",
    "WAITING",
    "CLAIMED",
    "MISSED",
    "ARCHIVED",
)

# Legacy + product aliases → canonical PROJECT_STAGES
_STAGE_ALIASES = {
    "discovered": "DISCOVERED",
    "researching": "RESEARCHING",
    "farming": "FARMING",
    "watchlist": "WATCHLIST",
    "monitoring": "WATCHLIST",
    "watching": "WATCHLIST",
    "waiting for tge": "WAITING FOR TGE",
    "tge soon": "WAITING FOR TGE",
    "completed": "COMPLETED",
    "archived": "ARCHIVED",
}

_STATUS_TO_STAGE = {
    "researching": "RESEARCHING",
    "watching": "WATCHLIST",
    "archived": "ARCHIVED",
    "discovered": "DISCOVERED",
    "farming": "FARMING",
    "monitoring": "WATCHLIST",
    "watchlist": "WATCHLIST",
    "tge soon": "WAITING FOR TGE",
    "waiting for tge": "WAITING FOR TGE",
    "completed": "COMPLETED",
}

_AIRDROP_STATUS_MAP = {
    "discovered": "DISCOVERED",
    "researching": "RESEARCHING",
    "active": "ACTIVE",
    "farming": "ACTIVE",
    "claim available": "ACTIVE",
    "eligible": "ACTIVE",
    "waiting": "WAITING",
    "tge soon": "WAITING",
    "claimed": "CLAIMED",
    "completed": "COMPLETED",
    "missed": "MISSED",
    "dead": "MISSED",
    "archived": "ARCHIVED",
    "watching": "DISCOVERED",
}


def normalize_project_stage(stage: str | None = None, status: str | None = None) -> str:
    """Map legacy / display aliases to canonical PROJECT_STAGES value."""
    s = (stage or "").strip()
    if s:
        mapped = _STAGE_ALIASES.get(s.lower())
        if mapped:
            return mapped
        if s in PROJECT_STAGES:
            return s
    if status:
        mapped = _STATUS_TO_STAGE.get(str(status).lower()) or _STAGE_ALIASES.get(str(status).lower())
        if mapped:
            return mapped
    return "RESEARCHING"


def normalize_airdrop_status(status: str | None = None) -> str:
    """Map legacy airdrop status strings to canonical AIRDROP_STATUSES."""
    s = (status or "").strip()
    if not s:
        return "DISCOVERED"
    if s in AIRDROP_STATUSES:
        return s
    return _AIRDROP_STATUS_MAP.get(s.lower(), s if s in AIRDROP_STATUSES else "DISCOVERED")



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
        ("stage", "TEXT DEFAULT 'RESEARCHING'"),
        ("ticker", "TEXT DEFAULT ''"),
        ("twitter", "TEXT DEFAULT ''"),
        ("discord", "TEXT DEFAULT ''"),
        ("telegram", "TEXT DEFAULT ''"),
        ("github", "TEXT DEFAULT ''"),
        ("blog", "TEXT DEFAULT ''"),
        ("research_notes", "TEXT DEFAULT ''"),
        ("risk_notes", "TEXT DEFAULT ''"),
        ("personal_rating", "INTEGER DEFAULT 0"),
        ("launch_status", "TEXT DEFAULT ''"),
        ("token_status", "TEXT DEFAULT ''"),
        ("tags", "TEXT DEFAULT ''"),
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
        ("funding", "TEXT DEFAULT ''"),
        ("investors", "TEXT DEFAULT ''"),
        ("risk", "TEXT DEFAULT ''"),
        ("last_checked", "TEXT DEFAULT ''"),
        ("priority", "INTEGER DEFAULT 3"),
    ]:
        _ensure_column(conn, "airdrops", col, typedef)

    _ensure_column(conn, "partner_link_clicks", "source_page", "TEXT DEFAULT ''")

    # v2.6.0 — normalize legacy partner categories (Wallet→Wallets, etc.)
    try:
        from mccc.partners import migrate_partner_categories
        # migrate uses its own connect; do inline UPDATE here to stay in this txn
        alias = {
            "Wallet": "Wallets",
            "Crypto Tool": "Tools",
            "Partner": "Tools",
            "Explorer": "Explorers",
        }
        for old, new in alias.items():
            conn.execute(
                "UPDATE partner_links SET category=? WHERE category=?",
                (new, old),
            )
            conn.execute(
                "UPDATE partner_link_clicks SET category=? WHERE category=?",
                (new, old),
            )
    except Exception:
        pass


    # Normalize project stages (legacy Title Case / aliases → canonical)
    rows = conn.execute("SELECT id, status, stage FROM projects").fetchall()
    for r in rows:
        new_stage = normalize_project_stage(r["stage"], r["status"])
        if (r["stage"] or "").strip() != new_stage:
            conn.execute("UPDATE projects SET stage=? WHERE id=?", (new_stage, r["id"]))

    # Normalize airdrop statuses
    arows = conn.execute("SELECT id, status FROM airdrops").fetchall()
    for r in arows:
        new_status = normalize_airdrop_status(r["status"])
        if (r["status"] or "").strip() != new_status:
            conn.execute("UPDATE airdrops SET status=? WHERE id=?", (new_status, r["id"]))

    # research_notes: link optional project_id (MCCC 2.0)
    _ensure_column(conn, "research_notes", "project_id", "INTEGER")

    # users soft-delete (Phase 12)
    _ensure_column(conn, "users", "deleted_at", "TEXT")

    # Ensure 2.0 tables exist on upgraded DBs (CREATE IF NOT EXISTS is idempotent)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS exchanges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT 'CEX',
        official_url TEXT NOT NULL DEFAULT '',
        referral_url TEXT DEFAULT '',
        docs_url TEXT DEFAULT '',
        chains TEXT DEFAULT '',
        assets TEXT DEFAULT '',
        region TEXT DEFAULT '',
        difficulty TEXT DEFAULT '',
        security_info TEXT DEFAULT '',
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Active',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT NOT NULL DEFAULT '',
        resource_type TEXT DEFAULT '',
        project_id INTEGER,
        description TEXT DEFAULT '',
        is_official INTEGER NOT NULL DEFAULT 0,
        click_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        body TEXT DEFAULT '',
        published INTEGER NOT NULL DEFAULT 0,
        expires_at TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL,
        item_ref TEXT NOT NULL,
        notes TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        priority INTEGER DEFAULT 3,
        favourite INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS research_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        event_type TEXT NOT NULL DEFAULT 'note',
        body TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS project_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT DEFAULT '',
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        event_type TEXT NOT NULL DEFAULT 'important',
        event_date TEXT NOT NULL,
        end_date TEXT DEFAULT '',
        entity_type TEXT DEFAULT '',
        entity_ref TEXT DEFAULT '',
        project_id INTEGER,
        airdrop_id INTEGER,
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        data_quality TEXT DEFAULT 'UNKNOWN',
        is_demo INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_calendar_events_date ON calendar_events(event_date);
    CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON calendar_events(event_type);
    """)


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
    from mccc.exchanges import seed_demo_exchanges

    seed_demo_exchanges(db_path)
    # Intelligence Agent Phase 1 — schema + DEMO seed (never auto-mixed as live)
    try:
        from mccc.intelligence.pipeline import IntelligencePipeline

        IntelligencePipeline(db_path).seed_demo_if_empty()
    except Exception:
        pass
    try:
        from mccc.intelligence.rwa.service import RWAService

        RWAService(db_path).seed_demo_if_empty()
    except Exception:
        pass
    try:
        ensure_calendar_schema(db_path)
        seed_demo_calendar_events(db_path)
    except Exception:
        pass


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
        ("DEMO: Layer-2 Research Brief", "ethereum", "researching", "RESEARCHING", "EXAMPLE notes — compare fees, TVL, bridge risk.", 2),
        ("DEMO: DeFi Protocol Diligence", "multi", "watching", "WATCHLIST", "EXAMPLE — read docs, audit status, token unlocks.", 3),
        ("DEMO: NFT Market Structure", "ethereum", "archived", "COMPLETED", "EXAMPLE case closed — education only.", 5),
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
        ("DEMO Protocol Alpha", "ethereum", "DISCOVERED", "EXAMPLE: testnet txs, Discord role — not live eligibility.", "DEMO / unknown", ""),
        ("DEMO Chain Beta Points", "solana", "ACTIVE", "EXAMPLE: points program notes for research practice.", "DEMO estimate only", "TBD"),
        ("DEMO Governance Gamma", "arbitrum", "CLAIMED", "EXAMPLE claimed entry — educational tracker.", "DEMO", "2024-01-01"),
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


PROJECT_EXTRA_FIELDS = {
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
    "ticker",
    "twitter",
    "discord",
    "telegram",
    "github",
    "blog",
    "research_notes",
    "risk_notes",
    "personal_rating",
    "launch_status",
    "token_status",
    "tags",
}

AIRDROP_EXTRA_FIELDS = {
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
    "funding",
    "investors",
    "risk",
    "last_checked",
    "priority",
}


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
    stage = normalize_project_stage(stage, status)
    extra_cols = {
        k: v
        for k, v in extra.items()
        if k in PROJECT_EXTRA_FIELDS
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
    } | PROJECT_EXTRA_FIELDS
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "stage" in updates:
        updates["stage"] = normalize_project_stage(updates["stage"], updates.get("status"))
    elif "status" in updates:
        updates["stage"] = normalize_project_stage(None, updates["status"])
    updates["updated_at"] = utc_now()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [project_id]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE projects SET {cols} WHERE id=?", vals)


def delete_project(project_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM research_events WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM project_tags WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))


# --- Airdrops ---

def list_airdrops(db_path: Optional[Path] = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM airdrops ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def add_airdrop(
    project_name: str,
    chain: str = "",
    status: str = "DISCOVERED",
    eligibility_notes: str = "",
    estimated_value: str = "DEMO / unknown",
    deadline: str = "",
    db_path: Optional[Path] = None,
    **extra: Any,
) -> int:
    now = utc_now()
    status = normalize_airdrop_status(status)
    extra_allowed = AIRDROP_EXTRA_FIELDS
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
    } | AIRDROP_EXTRA_FIELDS
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "status" in updates and updates["status"]:
        updates["status"] = normalize_airdrop_status(str(updates["status"]))
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
    from mccc.security import reject_sensitive_credential

    addr = address.strip()
    if not addr or " " in addr:
        raise ValueError("Address must be a non-empty public address string")
    reject_sensitive_credential(addr, field="wallet.address")
    reject_sensitive_credential(label, field="wallet.label")
    reject_sensitive_credential(notes or "", field="wallet.notes")
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


def add_note(
    title: str,
    body: str = "",
    tags: str = "",
    project_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> int:
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO research_notes (title, body, tags, project_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title.strip(), body, tags, project_id, now, now),
        )
        return int(cur.lastrowid)


# --- App settings (key/value) ---

def get_setting(key: str, default: str = "", db_path: Optional[Path] = None) -> str:
    with connect(db_path) as conn:
        row = conn.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
        return str(row["value"]) if row else default


def set_setting(key: str, value: str, db_path: Optional[Path] = None) -> None:
    now = utc_now()
    with connect(db_path) as conn:
        conn.execute(
            """INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, value, now),
        )


def list_settings(db_path: Optional[Path] = None) -> dict[str, str]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT key, value FROM app_settings ORDER BY key").fetchall()
        return {r["key"]: r["value"] for r in rows}

# --- Calendar events (Phase 1 foundation) ---

CALENDAR_EVENT_TYPES = (
    "airdrop",
    "unlock",
    "burn",
    "project",
    "governance",
    "important",
)


def ensure_calendar_schema(db_path: Optional[Path] = None) -> None:
    """Idempotent calendar_events table (also created via SCHEMA / migrate)."""
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL DEFAULT 'important',
                event_date TEXT NOT NULL,
                end_date TEXT DEFAULT '',
                entity_type TEXT DEFAULT '',
                entity_ref TEXT DEFAULT '',
                project_id INTEGER,
                airdrop_id INTEGER,
                description TEXT DEFAULT '',
                source TEXT DEFAULT '',
                data_quality TEXT DEFAULT 'UNKNOWN',
                is_demo INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_calendar_events_date ON calendar_events(event_date);
            CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON calendar_events(event_type);
            """
        )


def add_calendar_event(
    title: str,
    event_type: str,
    event_date: str,
    *,
    end_date: str = "",
    entity_type: str = "",
    entity_ref: str = "",
    project_id: Optional[int] = None,
    airdrop_id: Optional[int] = None,
    description: str = "",
    source: str = "",
    data_quality: str = "UNKNOWN",
    is_demo: bool = False,
    db_path: Optional[Path] = None,
) -> int:
    ensure_calendar_schema(db_path)
    now = utc_now()
    et = (event_type or "important").strip().lower()
    if et not in CALENDAR_EVENT_TYPES:
        et = "important"
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO calendar_events (
                title, event_type, event_date, end_date, entity_type, entity_ref,
                project_id, airdrop_id, description, source, data_quality, is_demo,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title.strip(),
                et,
                event_date.strip(),
                end_date or "",
                entity_type or "",
                entity_ref or "",
                project_id,
                airdrop_id,
                description or "",
                source or "",
                data_quality or "UNKNOWN",
                1 if is_demo else 0,
                now,
                now,
            ),
        )
        return int(cur.lastrowid)


def list_calendar_events(
    *,
    event_type: Optional[str] = None,
    month: Optional[str] = None,
    include_demo: bool = True,
    limit: int = 200,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    ensure_calendar_schema(db_path)
    clauses: list[str] = []
    params: list[Any] = []
    if event_type:
        clauses.append("event_type = ?")
        params.append(event_type.strip().lower())
    if month:
        # YYYY-MM prefix match on event_date
        clauses.append("event_date LIKE ?")
        params.append(f"{month.strip()}%")
    if not include_demo:
        clauses.append("is_demo = 0")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    with connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM calendar_events{where} ORDER BY event_date ASC, id ASC LIMIT ?",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def get_calendar_event(event_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    ensure_calendar_schema(db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM calendar_events WHERE id=?", (event_id,)).fetchone()
        return dict(row) if row else None


def delete_calendar_event(event_id: int, db_path: Optional[Path] = None) -> None:
    ensure_calendar_schema(db_path)
    with connect(db_path) as conn:
        conn.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))


def seed_demo_calendar_events(db_path: Optional[Path] = None) -> int:
    """Seed a few labelled DEMO calendar rows when table is empty. Returns count inserted."""
    ensure_calendar_schema(db_path)
    with connect(db_path) as conn:
        n = conn.execute("SELECT COUNT(*) AS c FROM calendar_events").fetchone()["c"]
        if n and int(n) > 0:
            return 0
    demos = [
        {
            "title": "DEMO · Sample governance vote window",
            "event_type": "governance",
            "event_date": "2026-09-15",
            "end_date": "2026-09-22",
            "description": "Labelled DEMO placeholder — not a real on-chain vote.",
            "source": "DEMO seed",
            "data_quality": "UNVERIFIED",
            "entity_type": "protocol",
            "entity_ref": "uniswap",
        },
        {
            "title": "DEMO · Research checkpoint (project)",
            "event_type": "project",
            "event_date": "2026-09-10",
            "description": "DEMO placeholder for calendar Month/List views.",
            "source": "DEMO seed",
            "data_quality": "UNVERIFIED",
            "entity_type": "project",
            "entity_ref": "demo-project",
        },
        {
            "title": "DEMO · Important research date",
            "event_type": "important",
            "event_date": "2026-09-30",
            "description": "DEMO — unlocks/burns/airdrops populate in later phases with sourced feeds.",
            "source": "DEMO seed",
            "data_quality": "UNVERIFIED",
        },
    ]
    inserted = 0
    for d in demos:
        add_calendar_event(
            d["title"],
            d["event_type"],
            d["event_date"],
            end_date=d.get("end_date", ""),
            entity_type=d.get("entity_type", ""),
            entity_ref=d.get("entity_ref", ""),
            description=d.get("description", ""),
            source=d.get("source", "DEMO seed"),
            data_quality=d.get("data_quality", "UNVERIFIED"),
            is_demo=True,
            db_path=db_path,
        )
        inserted += 1
    return inserted
