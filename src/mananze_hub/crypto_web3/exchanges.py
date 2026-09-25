"""Exchanges directory CRUD — official_url vs referral_url kept distinct."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now

TYPES = ("CEX", "DEX")
STATUSES = ("Active", "Disabled")


def resolve_visit_url(exchange: dict[str, Any] | Any) -> str:
    """Prefer non-empty referral_url; otherwise official_url. Never invent referrals."""
    if hasattr(exchange, "keys") and not isinstance(exchange, dict):
        exchange = dict(exchange)
    referral = (exchange.get("referral_url") or "").strip()
    official = (exchange.get("official_url") or "").strip()
    return referral if referral else official


def list_exchanges(
    status: Optional[str] = None,
    type_: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if type_:
        clauses.append("type = ?")
        params.append(type_)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM exchanges{where} ORDER BY type ASC, name ASC"
    with connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_exchange(exchange_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM exchanges WHERE id=?", (exchange_id,)).fetchone()
        return dict(row) if row else None


def add_exchange(
    name: str,
    type_: str = "CEX",
    official_url: str = "",
    referral_url: str = "",
    docs_url: str = "",
    chains: str = "",
    assets: str = "",
    region: str = "",
    difficulty: str = "",
    security_info: str = "",
    description: str = "",
    status: str = "Active",
    db_path: Optional[Path] = None,
) -> int:
    if type_ not in TYPES:
        raise ValueError(f"type must be one of {TYPES}")
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    name_n = (name or "").strip()
    if not name_n:
        raise ValueError("name is required")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO exchanges
               (name, type, official_url, referral_url, docs_url, chains, assets,
                region, difficulty, security_info, description, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name_n,
                type_,
                (official_url or "").strip(),
                (referral_url or "").strip(),
                docs_url or "",
                chains or "",
                assets or "",
                region or "",
                difficulty or "",
                security_info or "",
                description or "",
                status,
                now,
                now,
            ),
        )
        return int(cur.lastrowid)


def update_exchange(exchange_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    # Accept type as type_ from callers
    if "type_" in fields:
        fields["type"] = fields.pop("type_")
    allowed = {
        "name",
        "type",
        "official_url",
        "referral_url",
        "docs_url",
        "chains",
        "assets",
        "region",
        "difficulty",
        "security_info",
        "description",
        "status",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "type" in updates and updates["type"] not in TYPES:
        raise ValueError(f"type must be one of {TYPES}")
    if "status" in updates and updates["status"] not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    for url_key in ("official_url", "referral_url", "docs_url"):
        if url_key in updates and updates[url_key] is not None:
            updates[url_key] = str(updates[url_key]).strip()
    updates["updated_at"] = utc_now()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [exchange_id]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE exchanges SET {cols} WHERE id=?", vals)


def delete_exchange(exchange_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM exchanges WHERE id=?", (exchange_id,))


def set_exchange_status(exchange_id: int, status: str, db_path: Optional[Path] = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    update_exchange(exchange_id, status=status, db_path=db_path)


def seed_demo_exchanges(db_path: Optional[Path] = None) -> int:
    """Insert DEMO example.com exchange rows if table is empty. Returns count inserted."""
    with connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM exchanges").fetchone()
        if row and row["c"] > 0:
            return 0

    demos = [
        {
            "name": "DEMO Example CEX",
            "type_": "CEX",
            "official_url": "https://example.com/cex",
            "referral_url": "https://example.com/ref/cex-demo",
            "docs_url": "https://example.com/cex/docs",
            "chains": "Multi (DEMO)",
            "assets": "BTC, ETH, DEMO",
            "region": "Global (DEMO)",
            "difficulty": "Beginner",
            "security_info": "DEMO only — not a real exchange. Verify URLs yourself.",
            "description": "DEMO sample CEX listing. official_url ≠ referral_url on purpose.",
            "status": "Active",
        },
        {
            "name": "DEMO Example DEX",
            "type_": "DEX",
            "official_url": "https://example.com/dex",
            "referral_url": "",
            "docs_url": "https://example.com/dex/docs",
            "chains": "Ethereum, Arbitrum (DEMO)",
            "assets": "ERC-20 (DEMO)",
            "region": "On-chain",
            "difficulty": "Intermediate",
            "security_info": "DEMO — no contract addresses claimed. Never paste seed phrases into a DEX UI.",
            "description": "DEMO sample DEX with official URL only (empty referral).",
            "status": "Active",
        },
        {
            "name": "DEMO Research Spot",
            "type_": "CEX",
            "official_url": "https://example.com/spot",
            "referral_url": "",
            "docs_url": "",
            "chains": "DEMO-chain",
            "assets": "DEMO",
            "region": "Educational",
            "difficulty": "Beginner",
            "security_info": "Educational placeholder. Not KYC / not live markets.",
            "description": "DEMO third listing for directory UI practice.",
            "status": "Active",
        },
    ]
    count = 0
    for d in demos:
        add_exchange(db_path=db_path, **d)
        count += 1
    return count
