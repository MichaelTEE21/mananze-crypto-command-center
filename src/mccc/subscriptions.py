"""Local subscription / tier helpers — NO payment processing.

Stripe is Coming Soon. Never fake a successful payment.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now

TIERS = ("free", "pro")
PRO_PRICE_LABEL = "$4/mo"
PRO_PROVIDER = "coming_soon_stripe"


def get_subscription(user_id: Optional[int] = None, db_path: Optional[Path] = None) -> dict[str, Any]:
    """Return active subscription row or a synthetic free tier."""
    with connect(db_path) as conn:
        if user_id is None:
            row = conn.execute(
                """SELECT * FROM subscriptions
                   WHERE user_id IS NULL ORDER BY id DESC LIMIT 1"""
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT * FROM subscriptions
                   WHERE user_id=? ORDER BY id DESC LIMIT 1""",
                (user_id,),
            ).fetchone()
        if row:
            return dict(row)
    return {
        "id": None,
        "user_id": user_id,
        "tier": "free",
        "status": "active",
        "provider": PRO_PROVIDER,
        "created_at": None,
        "updated_at": None,
    }


def get_or_create_free(user_id: Optional[int] = None, db_path: Optional[Path] = None) -> dict[str, Any]:
    existing = get_subscription(user_id=user_id, db_path=db_path)
    if existing.get("id") is not None:
        return existing
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO subscriptions (user_id, tier, status, provider, created_at, updated_at)
               VALUES (?, 'free', 'active', ?, ?, ?)""",
            (user_id, PRO_PROVIDER, now, now),
        )
        return {
            "id": int(cur.lastrowid),
            "user_id": user_id,
            "tier": "free",
            "status": "active",
            "provider": PRO_PROVIDER,
            "created_at": now,
            "updated_at": now,
        }


def set_tier(
    tier: str,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Local-only tier toggle for architecture testing. Not a payment."""
    t = (tier or "free").strip().lower()
    if t not in TIERS:
        raise ValueError(f"tier must be one of {TIERS}")
    now = utc_now()
    sub = get_or_create_free(user_id=user_id, db_path=db_path)
    with connect(db_path) as conn:
        conn.execute(
            """UPDATE subscriptions SET tier=?, status='active', provider=?, updated_at=?
               WHERE id=?""",
            (t, PRO_PROVIDER, now, sub["id"]),
        )
    return get_subscription(user_id=user_id, db_path=db_path)


def is_pro(user_id: Optional[int] = None, db_path: Optional[Path] = None) -> bool:
    import os

    if os.environ.get("MCCC_PRO_UNLOCK", "0") == "1":
        return True
    sub = get_subscription(user_id=user_id, db_path=db_path)
    return str(sub.get("tier") or "").lower() == "pro" and str(sub.get("status") or "") == "active"
