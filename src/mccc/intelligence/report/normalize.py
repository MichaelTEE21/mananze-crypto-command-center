"""Normalise provider payloads into analytics-friendly structures."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mccc.intelligence.report.providers import ProviderResult


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_wallet(result: ProviderResult) -> dict[str, Any]:
    data = result.data or {}
    balances = list(data.get("balances") or [])
    tokens = []
    total_known_usd = 0.0
    usd_known = False
    for b in balances:
        amt = b.get("amount")
        usd = b.get("usd_value")
        tokens.append(
            {
                "token": b.get("token") or "UNKNOWN",
                "amount": amt,
                "usd_value": usd,
                "source": b.get("source") or result.source,
                "is_live": bool(b.get("is_live", result.is_live)),
            }
        )
        if usd is not None:
            try:
                total_known_usd += float(usd)
                usd_known = True
            except (TypeError, ValueError):
                pass
    return {
        "address": data.get("address"),
        "chain": data.get("chain") or "unknown",
        "balances": tokens,
        "balance_count": len(tokens),
        "total_known_usd": round(total_known_usd, 2) if usd_known else None,
        "provider_ok": result.ok,
        "provider_error": result.error,
        "is_live": result.is_live,
        "is_demo": result.is_demo,
        "rate_limited": result.rate_limited,
        "timed_out": result.timed_out,
        "partial": result.partial,
        "source": result.source,
        "normalized_at": utc_iso(),
    }


def normalize_token(result: ProviderResult) -> dict[str, Any]:
    data = result.data or {}
    tok = data.get("token") or {}
    return {
        "token_id": data.get("token_id") or tok.get("id"),
        "symbol": tok.get("symbol"),
        "name": tok.get("name"),
        "price": tok.get("current_price"),
        "change_24h": tok.get("price_change_percentage_24h"),
        "market_cap": tok.get("market_cap"),
        "provider_ok": result.ok,
        "provider_error": result.error,
        "is_live": result.is_live,
        "is_demo": result.is_demo,
        "rate_limited": result.rate_limited,
        "timed_out": result.timed_out,
        "partial": result.partial,
        "source": result.source,
        "verification": "verified" if result.is_live else ("estimated" if result.is_demo else "unknown"),
        "normalized_at": utc_iso(),
    }


def normalize_project(result: ProviderResult) -> dict[str, Any]:
    data = result.data or {}
    proj = data.get("project")
    return {
        "project": proj,
        "hits": data.get("hits") or [],
        "provider_ok": result.ok,
        "provider_error": result.error,
        "is_demo": result.is_demo,
        "partial": result.partial,
        "source": result.source,
        "normalized_at": utc_iso(),
    }


def normalize_protocol(result: ProviderResult) -> dict[str, Any]:
    data = result.data or {}
    return {
        "project": data.get("project"),
        "hits": data.get("hits") or [],
        "events": data.get("events") or [],
        "tvl": data.get("tvl"),
        "tvl_note": data.get("tvl_note") or "DATA UNAVAILABLE",
        "provider_ok": result.ok,
        "provider_error": result.error,
        "is_demo": result.is_demo,
        "partial": result.partial,
        "source": result.source,
        "normalized_at": utc_iso(),
    }


def normalize_rwa(result: ProviderResult) -> dict[str, Any]:
    data = result.data or {}
    profile = data.get("profile")
    return {
        "profile": profile,
        "hits": data.get("hits") or [],
        "provider_ok": result.ok,
        "provider_error": result.error,
        "is_demo": result.is_demo or bool(profile and profile.get("is_demo")),
        "partial": result.partial,
        "source": result.source,
        "normalized_at": utc_iso(),
    }
