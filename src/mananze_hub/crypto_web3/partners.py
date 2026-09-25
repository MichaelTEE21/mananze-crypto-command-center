"""Centralized partner / referral link management — SQLite-backed, privacy-conscious.

Single source of truth for Crypto Directory outbound URLs.
Never hardcode partner/referral URLs in pages — always resolve through this module.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now

# v2.6.0 Crypto Directory categories (canonical)
CATEGORIES = ("Wallets", "CEX", "DEX", "Explorers", "Tools", "Education")
STATUSES = ("Active", "Disabled")

# Legacy → canonical (pre-2.6.0 rows)
CATEGORY_ALIASES: dict[str, str] = {
    "Wallet": "Wallets",
    "Wallets": "Wallets",
    "CEX": "CEX",
    "DEX": "DEX",
    "Explorers": "Explorers",
    "Explorer": "Explorers",
    "Crypto Tool": "Tools",
    "Tools": "Tools",
    "Partner": "Tools",
    "Education": "Education",
}

CTA_LABELS = {
    "Wallets": "Download / Visit Wallet",
    "CEX": "Join Exchange",
    "DEX": "Explore DEX",
    "Explorers": "Open Explorer",
    "Tools": "Visit Platform",
    "Education": "Start Learning",
}

SECTION_TITLES = {
    "Wallets": "WALLETS",
    "CEX": "CENTRALIZED EXCHANGES",
    "DEX": "DECENTRALIZED EXCHANGES",
    "Explorers": "BLOCK EXPLORERS",
    "Tools": "CRYPTO TOOLS",
    "Education": "EDUCATION",
}

AFFILIATE_DISCLOSURE = (
    "Some links on MCCC may be partner or referral links. MCCC may receive compensation "
    "if you sign up through eligible links, at no additional cost to you."
)

REFERRAL_LEAVE_DISCLOSURE = (
    "You are leaving MCCC for an external platform. Always verify the official URL yourself. "
    "MCCC does not custody funds and never asks for seed phrases or private keys. "
    "A referral or partner link does **not** mean the destination is safer, better, or more profitable."
)

SEED_PHRASE_WARNING = "MCCC will never ask for your seed phrase or private keys."

# Postgres note (documented for operators — SQLite remains default)
POSTGRES_NOTE = (
    "Partner tables today use SQLite (`partner_links`, `partner_link_clicks`). "
    "A future Postgres migration can map 1:1 without schema invention; keep SQLite working."
)


def normalize_partner_category(category: str | None) -> str:
    """Map legacy category labels to canonical v2.6 categories."""
    raw = (category or "").strip()
    if not raw:
        return "Tools"
    if raw in CATEGORIES:
        return raw
    mapped = CATEGORY_ALIASES.get(raw)
    if mapped:
        return mapped
    # case-insensitive fallback
    lower_map = {k.lower(): v for k, v in CATEGORY_ALIASES.items()}
    return lower_map.get(raw.lower(), raw if raw in CATEGORIES else "Tools")


def cta_label(category: str) -> str:
    return CTA_LABELS.get(normalize_partner_category(category), "Visit Platform")


def section_title(category: str) -> str:
    return SECTION_TITLES.get(normalize_partner_category(category), "PLATFORMS")


def resolve_visit_url(link: dict[str, Any] | Any) -> str:
    """Prefer non-empty referral_url; otherwise official_url. Never invent referrals."""
    if hasattr(link, "keys") and not isinstance(link, dict):
        link = dict(link)
    referral = (link.get("referral_url") or "").strip()
    official = (link.get("official_url") or "").strip()
    return referral if referral else official


def resolve_outbound(
    link: dict[str, Any] | Any,
    *,
    require_active: bool = False,
) -> dict[str, Any]:
    """Central routing decision for Join/Download CTAs.

    Returns dict with url, used_referral, official_url, status, category, name.
    If require_active and status != Active, still returns official_url only (safe fallback).
    """
    if hasattr(link, "keys") and not isinstance(link, dict):
        link = dict(link)
    official = (link.get("official_url") or "").strip()
    referral = (link.get("referral_url") or "").strip()
    status = (link.get("status") or "Active").strip()
    used_referral = bool(referral)
    if require_active and status != "Active":
        url = official
        used_referral = False
    else:
        url = referral if referral else official
    return {
        "url": url,
        "used_referral": used_referral and bool(url),
        "official_url": official,
        "referral_url": referral,
        "status": status,
        "category": normalize_partner_category(link.get("category")),
        "name": link.get("name") or "",
        "id": link.get("id"),
    }


def get_outbound_url(
    link_id: int,
    db_path: Optional[Path] = None,
    *,
    require_active: bool = True,
) -> Optional[dict[str, Any]]:
    """Resolve outbound URL by id via the central partner-link service."""
    link = get_partner_link(link_id, db_path=db_path)
    if not link:
        return None
    return resolve_outbound(link, require_active=require_active)


def list_partner_links(
    status: Optional[str] = None,
    category: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if category:
        canon = normalize_partner_category(category)
        # Match canonical + any legacy labels that map here (pre-migration rows)
        aliases = sorted({k for k, v in CATEGORY_ALIASES.items() if v == canon} | {canon})
        placeholders = ", ".join("?" for _ in aliases)
        clauses.append(f"category IN ({placeholders})")
        params.extend(aliases)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM partner_links{where} ORDER BY category ASC, name ASC"
    with connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["category"] = normalize_partner_category(d.get("category"))
            out.append(d)
        return out


def get_partner_link(link_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM partner_links WHERE id=?", (link_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["category"] = normalize_partner_category(d.get("category"))
        return d


def add_partner_link(
    name: str,
    category: str,
    official_url: str,
    referral_url: str = "",
    description: str = "",
    features: str = "",
    networks: str = "",
    logo_url: str = "",
    status: str = "Active",
    db_path: Optional[Path] = None,
) -> int:
    category = normalize_partner_category(category)
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of {CATEGORIES}")
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    referral = (referral_url or "").strip()
    is_referral = 1 if referral else 0
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO partner_links
               (name, category, official_url, referral_url, description, features,
                networks, logo_url, status, is_referral, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name.strip(),
                category,
                official_url.strip(),
                referral,
                description,
                features,
                networks,
                logo_url,
                status,
                is_referral,
                now,
                now,
            ),
        )
        return int(cur.lastrowid)


def update_partner_link(link_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    allowed = {
        "name",
        "category",
        "official_url",
        "referral_url",
        "description",
        "features",
        "networks",
        "logo_url",
        "status",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "category" in updates:
        updates["category"] = normalize_partner_category(updates["category"])
        if updates["category"] not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
    if "status" in updates and updates["status"] not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if "referral_url" in updates:
        ref = (updates["referral_url"] or "").strip()
        updates["referral_url"] = ref
        updates["is_referral"] = 1 if ref else 0
    updates["updated_at"] = utc_now()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [link_id]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE partner_links SET {cols} WHERE id=?", vals)


def upsert_partner_link(
    name: str,
    category: str,
    official_url: str,
    referral_url: str = "",
    description: str = "",
    features: str = "",
    networks: str = "",
    logo_url: str = "",
    status: str = "Active",
    link_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> int:
    if link_id:
        update_partner_link(
            link_id,
            name=name,
            category=category,
            official_url=official_url,
            referral_url=referral_url,
            description=description,
            features=features,
            networks=networks,
            logo_url=logo_url,
            status=status,
            db_path=db_path,
        )
        return link_id
    return add_partner_link(
        name=name,
        category=category,
        official_url=official_url,
        referral_url=referral_url,
        description=description,
        features=features,
        networks=networks,
        logo_url=logo_url,
        status=status,
        db_path=db_path,
    )


def set_partner_status(link_id: int, status: str, db_path: Optional[Path] = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    update_partner_link(link_id, status=status, db_path=db_path)


def delete_partner_link(link_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM partner_link_clicks WHERE partner_link_id=?", (link_id,))
        conn.execute("DELETE FROM partner_links WHERE id=?", (link_id,))


def record_click(
    link_id: int,
    db_path: Optional[Path] = None,
    source_page: str = "",
) -> None:
    """Privacy-conscious click: platform id, category, timestamp, optional source_page — no IP/UA/PII."""
    link = get_partner_link(link_id, db_path=db_path)
    if not link:
        raise ValueError(f"partner link {link_id} not found")
    cat = normalize_partner_category(link["category"])
    with connect(db_path) as conn:
        conn.execute(
            """INSERT INTO partner_link_clicks (partner_link_id, category, clicked_at, source_page)
               VALUES (?, ?, ?, ?)""",
            (link_id, cat, utc_now(), source_page or ""),
        )


def click_analytics(db_path: Optional[Path] = None) -> dict[str, Any]:
    """Aggregates only: total, per platform, per category, per date — no PII."""
    with connect(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM partner_link_clicks").fetchone()["c"]
        per_platform = conn.execute(
            """SELECT pl.id, pl.name, pl.category, COUNT(c.id) AS clicks
               FROM partner_links pl
               LEFT JOIN partner_link_clicks c ON c.partner_link_id = pl.id
               GROUP BY pl.id
               ORDER BY clicks DESC, pl.name ASC"""
        ).fetchall()
        per_category = conn.execute(
            """SELECT category, COUNT(*) AS clicks
               FROM partner_link_clicks
               GROUP BY category
               ORDER BY clicks DESC"""
        ).fetchall()
        per_date = conn.execute(
            """SELECT substr(clicked_at, 1, 10) AS day, COUNT(*) AS clicks
               FROM partner_link_clicks
               GROUP BY day
               ORDER BY day DESC
               LIMIT 90"""
        ).fetchall()
    cat_map: dict[str, int] = {}
    for r in per_category:
        canon = normalize_partner_category(r["category"])
        cat_map[canon] = cat_map.get(canon, 0) + int(r["clicks"])
    category_counts = {cat: int(cat_map.get(cat, 0)) for cat in CATEGORIES}
    for cat, n in cat_map.items():
        if cat not in category_counts:
            category_counts[cat] = int(n)
    platforms = []
    for r in per_platform:
        d = dict(r)
        d["category"] = normalize_partner_category(d.get("category"))
        platforms.append(d)
    return {
        "total_clicks": int(total),
        "per_platform": platforms,
        "per_category": category_counts,
        "per_date": [dict(r) for r in per_date],
    }


def partner_ecosystem_summary(db_path: Optional[Path] = None) -> dict[str, Any]:
    """Lightweight counts for Command Center partner ecosystem strip."""
    active = list_partner_links(status="Active", db_path=db_path)
    by_cat = {c: 0 for c in CATEGORIES}
    for link in active:
        by_cat[normalize_partner_category(link.get("category"))] = (
            by_cat.get(normalize_partner_category(link.get("category")), 0) + 1
        )
    analytics = click_analytics(db_path=db_path)
    return {
        "active_total": len(active),
        "by_category": by_cat,
        "total_clicks": analytics["total_clicks"],
    }


def migrate_partner_categories(db_path: Optional[Path] = None) -> int:
    """Rewrite legacy category labels to canonical. Returns rows updated."""
    updated = 0
    with connect(db_path) as conn:
        rows = conn.execute("SELECT id, category FROM partner_links").fetchall()
        for r in rows:
            canon = normalize_partner_category(r["category"])
            if (r["category"] or "") != canon:
                conn.execute(
                    "UPDATE partner_links SET category=?, updated_at=? WHERE id=?",
                    (canon, utc_now(), r["id"]),
                )
                updated += 1
        # Also normalize historical click category labels
        clicks = conn.execute("SELECT id, category FROM partner_link_clicks").fetchall()
        for r in clicks:
            canon = normalize_partner_category(r["category"])
            if (r["category"] or "") != canon:
                conn.execute(
                    "UPDATE partner_link_clicks SET category=? WHERE id=?",
                    (canon, r["id"]),
                )
    return updated


def seed_demo_partners(db_path: Optional[Path] = None) -> int:
    """Insert clearly labelled DEMO sample partners if the table is empty. Returns rows inserted."""
    with connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM partner_links").fetchone()
        if row and row["c"] > 0:
            # Still migrate any legacy labels on existing DBs
            pass
        else:
            demos = [
                {
                    "name": "DEMO Example Wallet",
                    "category": "Wallets",
                    "official_url": "https://example.com/wallet",
                    "referral_url": "",
                    "description": "DEMO sample — placeholder wallet listing for UI testing. Not a recommendation.",
                    "features": "DEMO, Self-custody education, Public info only",
                    "networks": "Ethereum, DEMO-chain",
                    "logo_url": "",
                    "status": "Active",
                },
                {
                    "name": "DEMO Example CEX",
                    "category": "CEX",
                    "official_url": "https://example.com/cex",
                    "referral_url": "https://example.com/ref/demo",
                    "description": "DEMO sample — fake referral path on example.com. Not a live affiliate offer.",
                    "features": "DEMO, Spot research notes, No KYC claims made here",
                    "networks": "Multi-chain (DEMO)",
                    "logo_url": "",
                    "status": "Active",
                },
                {
                    "name": "DEMO Example DEX",
                    "category": "DEX",
                    "official_url": "https://example.com/dex",
                    "referral_url": "",
                    "description": "DEMO sample — decentralized exchange placeholder. Verify contracts yourself.",
                    "features": "DEMO, Swap education, No profit claims",
                    "networks": "Ethereum, Arbitrum (DEMO)",
                    "logo_url": "",
                    "status": "Active",
                },
                {
                    "name": "DEMO Block Explorer",
                    "category": "Explorers",
                    "official_url": "https://example.com/explorer",
                    "referral_url": "",
                    "description": "DEMO sample — explorer listing. Prefer in-app Chain Explorers for lookups.",
                    "features": "DEMO, Public address lookup education",
                    "networks": "Ethereum (DEMO)",
                    "logo_url": "",
                    "status": "Active",
                },
                {
                    "name": "DEMO Crypto Tool",
                    "category": "Tools",
                    "official_url": "https://example.com/tool",
                    "referral_url": "",
                    "description": "DEMO sample — research tooling placeholder. Educational only.",
                    "features": "DEMO, Portfolio notes, Explorer links",
                    "networks": "Multi",
                    "logo_url": "",
                    "status": "Active",
                },
                {
                    "name": "DEMO Education Partner",
                    "category": "Education",
                    "official_url": "https://example.com/learn",
                    "referral_url": "",
                    "description": "DEMO sample — education partner card. Not endorsed as safer/more profitable.",
                    "features": "DEMO, Education, Disclosure practice",
                    "networks": "N/A",
                    "logo_url": "",
                    "status": "Active",
                },
                {
                    "name": "CoinGecko (official)",
                    "category": "Tools",
                    "official_url": "https://www.coingecko.com",
                    "referral_url": "",
                    "description": "DEMO directory entry pointing at the public CoinGecko site — empty referral for honesty.",
                    "features": "Market data, Charts, Public API docs",
                    "networks": "Multi-chain data",
                    "logo_url": "",
                    "status": "Active",
                },
            ]
            count = 0
            for d in demos:
                add_partner_link(db_path=db_path, **d)
                count += 1
            migrate_partner_categories(db_path=db_path)
            return count
    migrate_partner_categories(db_path=db_path)
    return 0
