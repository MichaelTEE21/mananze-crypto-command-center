"""Local subscription / tier helpers — NO payment processing.

Stripe is Coming Soon. Never fake a successful payment.

FREE soft limits (guest or free tier) apply when PRO is not active.
PRO unlock paths: local tier=pro, feature_flags, or ``MCCC_PRO_UNLOCK=1``.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, is_feature_enabled, utc_now

TIERS = ("free", "pro")
PRO_PRICE_LABEL = "$4/mo"
PRO_PROVIDER = "coming_soon_stripe"
PRO_PAYMENTS_MESSAGE = "PRO payments are not yet enabled."

# Soft FREE limits — constants (override via env optional ints)
FREE_MAX_PROJECTS = int(os.environ.get("MCCC_FREE_MAX_PROJECTS", "10"))
FREE_MAX_WALLETS = int(os.environ.get("MCCC_FREE_MAX_WALLETS", "5"))
FREE_MAX_AIRDROPS = int(os.environ.get("MCCC_FREE_MAX_AIRDROPS", "15"))

LIMIT_KEYS = {
    "projects": FREE_MAX_PROJECTS,
    "wallets": FREE_MAX_WALLETS,
    "airdrops": FREE_MAX_AIRDROPS,
}

PRO_FEATURES = (
    "pro_advanced_analytics",
    "pro_wallet_alerts",
    "pro_ai_deep_research",
    "pro_portfolio_sync",
)


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
    if os.environ.get("MCCC_PRO_UNLOCK", "0") == "1":
        return True
    sub = get_subscription(user_id=user_id, db_path=db_path)
    return str(sub.get("tier") or "").lower() == "pro" and str(sub.get("status") or "") == "active"


def has_pro_feature(
    feature_key: str,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """PRO access for a named feature: unlock env, pro tier, or feature flag."""
    if is_pro(user_id=user_id, db_path=db_path):
        return True
    return is_feature_enabled(feature_key, db_path=db_path)


def free_limits() -> dict[str, int]:
    return {
        "projects": FREE_MAX_PROJECTS,
        "wallets": FREE_MAX_WALLETS,
        "airdrops": FREE_MAX_AIRDROPS,
    }


def count_resource(resource: str, db_path: Optional[Path] = None) -> int:
    """Count local inventory rows for soft-limit checks (all users / guest shared DB)."""
    table = {
        "projects": "projects",
        "wallets": "wallets",
        "airdrops": "airdrops",
    }.get(resource)
    if not table:
        raise ValueError(f"Unknown resource: {resource}")
    with connect(db_path) as conn:
        row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
        return int(row["c"] if row else 0)


def check_limit(
    resource: str,
    user_id: Optional[int] = None,
    *,
    db_path: Optional[Path] = None,
    current_count: Optional[int] = None,
) -> dict[str, Any]:
    """Soft-gate check. PRO / unlock -> unlimited.

    Returns dict: allowed, resource, limit, count, remaining, message, upgrade_cta
    """
    if resource not in LIMIT_KEYS:
        raise ValueError(f"Unknown resource: {resource}")
    limit = LIMIT_KEYS[resource]
    if is_pro(user_id=user_id, db_path=db_path):
        count = current_count if current_count is not None else count_resource(resource, db_path=db_path)
        return {
            "allowed": True,
            "resource": resource,
            "limit": None,
            "count": count,
            "remaining": None,
            "unlimited": True,
            "message": "PRO · unlimited",
            "upgrade_cta": False,
        }
    count = current_count if current_count is not None else count_resource(resource, db_path=db_path)
    allowed = count < limit
    remaining = max(0, limit - count)
    if allowed:
        msg = f"Free tier: {count}/{limit} {resource} used ({remaining} left)."
    else:
        msg = (
            f"Free tier limit reached ({limit} {resource}). "
            f"Upgrade to PRO ({PRO_PRICE_LABEL}) for unlimited — "
            f"{PRO_PAYMENTS_MESSAGE}"
        )
    return {
        "allowed": allowed,
        "resource": resource,
        "limit": limit,
        "count": count,
        "remaining": remaining,
        "unlimited": False,
        "message": msg,
        "upgrade_cta": not allowed,
    }


def require_can_add(
    resource: str,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Raise ValueError with upgrade CTA copy when free limit hit."""
    result = check_limit(resource, user_id=user_id, db_path=db_path)
    if not result["allowed"]:
        raise ValueError(result["message"])
    return result


def upgrade_cta_markdown() -> str:
    return (
        f"**Upgrade to PRO · {PRO_PRICE_LABEL}** — Coming Soon. "
        f"{PRO_PAYMENTS_MESSAGE} "
        "Open the PRO Architecture page, or set `MCCC_PRO_UNLOCK=1` locally (architecture only, not payment)."
    )
