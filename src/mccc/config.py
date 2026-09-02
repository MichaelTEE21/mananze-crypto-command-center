"""Lightweight startup config validation — warn only, never crash.

Optional API keys and feature toggles. Never requires secrets to boot.
Never accepts or logs seed phrases / private keys / passwords.
"""
from __future__ import annotations

import os
from typing import Any

# Optional env keys — missing = warning only
OPTIONAL_ENV = (
    ("COINGECKO_API_KEY", "CoinGecko Pro key (free API works without it)"),
    ("ETHERSCAN_API_KEY", "Explorer balances for wallet tracking"),
    ("AI_API_KEY", "Optional LLM for AI assistant (rule-based works without)"),
    ("AI_API_BASE", "OpenAI-compatible base URL"),
    ("AI_MODEL", "LLM model id"),
    ("AUTH_SECRET", "Session salt (ephemeral generated if unset)"),
    ("MCCC_ADMIN_PASSWORD", "Admin gate (DEMO default if unset)"),
    ("MCCC_BOOTSTRAP_ADMIN_EMAIL", "Promote matching user to is_admin on boot"),
    ("MCCC_PRO_UNLOCK", "Set 1 to unlock PRO locally (not payment)"),
    ("MCCC_DEV", "Set 1 to enable Diagnostics page / Admin diagnostics"),
    ("MCCC_BTC_DONATION_ADDRESS", "Public BTC donation address (has default)"),
    ("MCCC_ETH_DONATION_ADDRESS", "Public ETH donation address (has default)"),
    ("MCCC_SOL_DONATION_ADDRESS", "Public SOL donation address (has default)"),
)

# Keys that must NEVER be treated as required for startup
NEVER_REQUIRED = frozenset(
    {
        "COINGECKO_API_KEY",
        "ETHERSCAN_API_KEY",
        "AI_API_KEY",
        "STRIPE_SECRET",
        "STRIPE_KEY",
        "DATABASE_URL",
    }
)


def env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip() in ("1", "true", "True", "yes", "YES")


def validate_config(*, as_dict: bool = False) -> list[str] | dict[str, Any]:
    """Return human-readable warnings for missing optional config.

    Never raises. Never crashes the app. Safe to call at every page_setup.
    """
    warnings: list[str] = []
    status: dict[str, Any] = {"ok": True, "warnings": warnings, "flags": {}}

    for key, purpose in OPTIONAL_ENV:
        val = os.environ.get(key, "").strip()
        present = bool(val)
        status["flags"][key] = {
            "set": present,
            "purpose": purpose,
            # Never echo secret values
            "preview": "(set)" if present else "(unset)",
        }
        if not present and key in (
            "AUTH_SECRET",
            "MCCC_ADMIN_PASSWORD",
        ):
            warnings.append(f"{key} unset — {purpose}")

    # Soft consistency checks
    if env_flag("MCCC_PRO_UNLOCK"):
        status["flags"]["pro_unlock_active"] = True
    if env_flag("MCCC_DEV"):
        status["flags"]["dev_mode"] = True

    # DATABASE_URL is ignored (SQLite local)
    if os.environ.get("DATABASE_URL", "").strip():
        warnings.append("DATABASE_URL is set but ignored — MCCC uses local SQLite")

    status["ok"] = True  # never fail startup
    if as_dict:
        return status
    return warnings


def config_status_public() -> dict[str, Any]:
    """Safe diagnostics snapshot — no secret values."""
    raw = validate_config(as_dict=True)
    assert isinstance(raw, dict)
    return {
        "ok": True,
        "warnings": list(raw.get("warnings") or []),
        "optional_keys": {
            k: {"set": v["set"], "purpose": v["purpose"]}
            for k, v in (raw.get("flags") or {}).items()
            if isinstance(v, dict) and "set" in v
        },
        "mccc_pro_unlock": env_flag("MCCC_PRO_UNLOCK"),
        "mccc_dev": env_flag("MCCC_DEV"),
        "bootstrap_admin_email_set": bool(
            os.environ.get("MCCC_BOOTSTRAP_ADMIN_EMAIL", "").strip()
        ),
    }
