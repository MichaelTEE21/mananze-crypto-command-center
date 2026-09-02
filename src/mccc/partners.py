"""Centralized partner / referral link management — SQLite-backed, privacy-conscious."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now

CATEGORIES = ("Wallet", "CEX", "DEX", "Crypto Tool", "Partner")
STATUSES = ("Active", "Disabled")

CTA_LABELS = {
    "Wallet": "Download / Visit Wallet",
    "CEX": "Join Exchange",
    "DEX": "Explore DEX",
    "Crypto Tool": "Visit Platform",
    "Partner": "Visit Platform",
}

AFFILIATE_DISCLOSURE = (
    "Some links on MCCC may be partner or referral links. MCCC may receive compensation "
    "if you sign up through eligible links, at no additional cost to you."
)

SEED_PHRASE_WARNING = "MCCC will never ask for your seed phrase or private keys."


def cta_label(category: str) -> str:
    return CTA_LABELS.get(category, "Visit Platform")


def resolve_visit_url(link: dict[str, Any] | Any) -> str:
    """Prefer non-empty referral_url; otherwise official_url."""
    if hasattr(link, "keys") and not isinstance(link, dict):
        link = dict(link)
    referral = (link.get("referral_url") or "").strip()
    official = (link.get("official_url") or "").strip()
    return referral if referral else official


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
        clauses.append("category = ?")
        params.append(category)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM partner_links{where} ORDER BY category ASC, name ASC"
    with connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_partner_link(link_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM partner_links WHERE id=?", (link_id,)).fetchone()
        return dict(row) if row else None


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
    if "category" in updates and updates["category"] not in CATEGORIES:
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


def record_click(link_id: int, db_path: Optional[Path] = None) -> None:
    link = get_partner_link(link_id, db_path=db_path)
    if not link:
        raise ValueError(f"partner link {link_id} not found")
    with connect(db_path) as conn:
        conn.execute(
            """INSERT INTO partner_link_clicks (partner_link_id, category, clicked_at)
               VALUES (?, ?, ?)""",
            (link_id, link["category"], utc_now()),
        )


def click_analytics(db_path: Optional[Path] = None) -> dict[str, Any]:
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
    # Ensure all known categories appear (zero-filled)
    cat_map = {r["category"]: r["clicks"] for r in per_category}
    category_counts = {cat: int(cat_map.get(cat, 0)) for cat in CATEGORIES}
    for cat, n in cat_map.items():
        if cat not in category_counts:
            category_counts[cat] = int(n)
    return {
        "total_clicks": int(total),
        "per_platform": [dict(r) for r in per_platform],
        "per_category": category_counts,
    }


def seed_demo_partners(db_path: Optional[Path] = None) -> int:
    """Insert clearly labelled DEMO sample partners if the table is empty. Returns rows inserted."""
    with connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM partner_links").fetchone()
        if row and row["c"] > 0:
            return 0

    demos = [
        {
            "name": "DEMO Example Wallet",
            "category": "Wallet",
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
            "name": "DEMO Crypto Tool",
            "category": "Crypto Tool",
            "official_url": "https://example.com/tool",
            "referral_url": "",
            "description": "DEMO sample — research tooling placeholder. Educational only.",
            "features": "DEMO, Portfolio notes, Explorer links",
            "networks": "Multi",
            "logo_url": "",
            "status": "Active",
        },
        {
            "name": "DEMO Research Partner",
            "category": "Partner",
            "official_url": "https://example.com/partner",
            "referral_url": "",
            "description": "DEMO sample — partner directory card. Not endorsed as safer/more profitable.",
            "features": "DEMO, Education, Disclosure practice",
            "networks": "N/A",
            "logo_url": "",
            "status": "Active",
        },
        {
            "name": "CoinGecko (official)",
            "category": "Crypto Tool",
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
    return count
