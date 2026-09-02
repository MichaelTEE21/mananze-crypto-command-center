"""Replaceable data providers for Intelligence Reports.

Wraps existing MCCC providers — never invents live numbers.
Failures return labelled DATA UNAVAILABLE / DEMO payloads.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass
class ProviderResult:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    is_live: bool = False
    is_demo: bool = False
    error: str = ""
    partial: bool = False
    rate_limited: bool = False
    timed_out: bool = False
    fetched_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.fetched_at:
            self.fetched_at = time.time()


@runtime_checkable
class ReportDataProvider(Protocol):
    name: str

    def fetch_wallet(self, address: str, chain: str = "ethereum") -> ProviderResult: ...

    def fetch_token(self, token_id_or_symbol: str) -> ProviderResult: ...

    def fetch_project(self, name: str) -> ProviderResult: ...

    def fetch_protocol(self, name: str) -> ProviderResult: ...

    def fetch_rwa(self, name: str) -> ProviderResult: ...

    def fetch_intel_events(self, query: str, limit: int = 10) -> ProviderResult: ...


class MCCCReportProvider:
    """Default provider composing wallets / market_provider / db / RWA / intel."""

    name = "mccc_default"

    def __init__(self, *, timeout: float = 8.0, db_path=None) -> None:
        self.timeout = timeout
        self.db_path = db_path

    def fetch_wallet(self, address: str, chain: str = "ethereum") -> ProviderResult:
        try:
            from mccc.wallets import balance_rows_for_address

            rows = balance_rows_for_address(address, chain=chain)
            if not rows:
                return ProviderResult(
                    ok=False,
                    source="wallet_provider",
                    error="DATA UNAVAILABLE — no balance rows returned",
                    partial=True,
                )
            # DEMO addresses or DEMO fallback source
            is_demo = bool(address.startswith("0xDEMO")) or any(
                (not r.get("is_live", False)) and "DEMO" in str(r.get("source", "")).upper()
                for r in rows
            )
            any_live = any(bool(r.get("is_live")) for r in rows)
            # If all zero and source says unavailable
            if len(rows) == 1 and rows[0].get("usd_value") is None and not any_live:
                src = str(rows[0].get("source") or "")
                if "unavailable" in src.lower() or "fallback" in src.lower():
                    return ProviderResult(
                        ok=False,
                        data={"balances": rows, "address": address, "chain": chain},
                        source=src or "wallet_provider",
                        is_live=False,
                        is_demo=True,
                        error="DATA UNAVAILABLE — public balance lookup unavailable",
                        partial=True,
                    )
            return ProviderResult(
                ok=True,
                data={"balances": rows, "address": address, "chain": chain},
                source=str(rows[0].get("source") or "wallet_provider"),
                is_live=any_live and not address.startswith("0xDEMO"),
                is_demo=is_demo or address.startswith("0xDEMO"),
                partial=not any_live,
            )
        except Exception as exc:
            msg = str(exc).lower()
            rate = "429" in msg or "rate" in msg
            timed = "timeout" in msg or "timed out" in msg
            return ProviderResult(
                ok=False,
                source="wallet_provider",
                error=f"DATA UNAVAILABLE — {exc}",
                rate_limited=rate,
                timed_out=timed,
            )

    def fetch_token(self, token_id_or_symbol: str) -> ProviderResult:
        try:
            from mccc.market_provider import get_default_provider

            provider = get_default_provider()
            # Map common symbols to coingecko ids
            aliases = {
                "btc": "bitcoin",
                "eth": "ethereum",
                "sol": "solana",
                "usdc": "usd-coin",
                "usdt": "tether",
            }
            tid = aliases.get(token_id_or_symbol.lower(), token_id_or_symbol.lower())
            rows, source, is_live = provider.get_prices(ids=tid)
            if not rows:
                return ProviderResult(
                    ok=False,
                    source=source or "market_provider",
                    error="DATA UNAVAILABLE — token not in provider response",
                    is_demo=not is_live,
                    partial=True,
                )
            row = rows[0]
            return ProviderResult(
                ok=True,
                data={"token": row, "token_id": tid},
                source=source,
                is_live=is_live,
                is_demo=not is_live,
            )
        except Exception as exc:
            msg = str(exc).lower()
            return ProviderResult(
                ok=False,
                source="market_provider",
                error=f"DATA UNAVAILABLE — {exc}",
                rate_limited="429" in msg or "rate" in msg,
                timed_out="timeout" in msg,
            )

    def fetch_project(self, name: str) -> ProviderResult:
        try:
            from mccc.db import list_projects
            from mccc.search import search_projects

            hits = search_projects(name, db_path=self.db_path, limit=10)
            all_p = list_projects(db_path=self.db_path) if not hits else hits
            # Prefer exact-ish name match
            needle = name.lower()
            exact = [p for p in hits if (p.get("name") or "").lower() == needle]
            chosen = exact[0] if exact else (hits[0] if hits else None)
            return ProviderResult(
                ok=True,
                data={"project": chosen, "hits": hits[:10], "local_count": len(all_p)},
                source="local_projects_db",
                is_live=False,
                is_demo=bool(chosen and "DEMO" in str(chosen.get("name", "")).upper()),
                partial=chosen is None,
                error="" if chosen else "No local project match — Insufficient data for on-chain claims",
            )
        except Exception as exc:
            return ProviderResult(ok=False, source="local_projects_db", error=f"DATA UNAVAILABLE — {exc}")

    def fetch_protocol(self, name: str) -> ProviderResult:
        # Protocols: reuse project search + intel events; no invented TVL
        proj = self.fetch_project(name)
        intel = self.fetch_intel_events(name, limit=8)
        data = {
            "project": (proj.data or {}).get("project"),
            "hits": (proj.data or {}).get("hits") or [],
            "events": (intel.data or {}).get("events") or [],
            "tvl": None,
            "tvl_note": "DATA UNAVAILABLE — no verified TVL provider wired; will not invent TVL",
        }
        return ProviderResult(
            ok=True,
            data=data,
            source="protocol_composite(local_projects+intel)",
            is_live=False,
            is_demo=proj.is_demo or intel.is_demo,
            partial=True,
            error="" if (data["project"] or data["events"]) else "Insufficient data",
        )

    def fetch_rwa(self, name: str) -> ProviderResult:
        try:
            from mccc.intelligence.rwa.service import RWAService

            svc = RWAService(self.db_path)
            svc.ensure_ready()
            hits = svc.search(name, limit=10)
            chosen = hits[0] if hits else None
            return ProviderResult(
                ok=True,
                data={"profile": chosen, "hits": hits},
                source="rwa_service",
                is_live=False,
                is_demo=bool(chosen and chosen.get("is_demo")),
                partial=chosen is None,
                error="" if chosen else "No RWA profile match — Insufficient data",
            )
        except Exception as exc:
            return ProviderResult(ok=False, source="rwa_service", error=f"DATA UNAVAILABLE — {exc}")

    def fetch_intel_events(self, query: str, limit: int = 10) -> ProviderResult:
        try:
            from mccc.search import search_intelligence

            hits = search_intelligence(query, db_path=self.db_path, limit=limit)
            return ProviderResult(
                ok=True,
                data={"events": hits},
                source="intelligence_repository",
                is_live=any(not h.get("is_demo") for h in hits) if hits else False,
                is_demo=all(h.get("is_demo") for h in hits) if hits else False,
                partial=not hits,
            )
        except Exception as exc:
            return ProviderResult(
                ok=False, source="intelligence_repository", error=f"DATA UNAVAILABLE — {exc}"
            )


class StaticDemoProvider:
    """Explicit DEMO provider for tests — always labelled synthetic."""

    name = "static_demo"

    def fetch_wallet(self, address: str, chain: str = "ethereum") -> ProviderResult:
        return ProviderResult(
            ok=True,
            data={
                "balances": [
                    {
                        "token": "ETH",
                        "amount": 1.0,
                        "usd_value": None,
                        "source": "DEMO / SYNTHETIC static provider",
                        "is_live": False,
                    }
                ],
                "address": address,
                "chain": chain,
            },
            source="DEMO / SYNTHETIC static provider",
            is_live=False,
            is_demo=True,
        )

    def fetch_token(self, token_id_or_symbol: str) -> ProviderResult:
        return ProviderResult(
            ok=True,
            data={
                "token": {
                    "id": f"demo-{token_id_or_symbol}",
                    "symbol": f"DEMO-{(token_id_or_symbol or 'X').upper()[:8]}",
                    "name": f"DEMO {token_id_or_symbol}",
                    "current_price": 1.0,
                    "market_cap": None,
                },
                "token_id": token_id_or_symbol,
            },
            source="DEMO / SYNTHETIC static provider",
            is_live=False,
            is_demo=True,
        )

    def fetch_project(self, name: str) -> ProviderResult:
        return ProviderResult(
            ok=True,
            data={
                "project": {
                    "id": 0,
                    "name": f"DEMO {name}",
                    "chain": "ethereum",
                    "stage": "discovered",
                    "notes": "DEMO / SYNTHETIC",
                },
                "hits": [],
            },
            source="DEMO / SYNTHETIC static provider",
            is_demo=True,
        )

    def fetch_protocol(self, name: str) -> ProviderResult:
        return ProviderResult(
            ok=True,
            data={
                "project": {"name": f"DEMO {name}", "notes": "DEMO / SYNTHETIC"},
                "events": [],
                "tvl": None,
                "tvl_note": "DATA UNAVAILABLE — DEMO provider does not invent TVL",
            },
            source="DEMO / SYNTHETIC static provider",
            is_demo=True,
            partial=True,
        )

    def fetch_rwa(self, name: str) -> ProviderResult:
        return ProviderResult(
            ok=True,
            data={
                "profile": {
                    "name": f"DEMO {name}",
                    "category": "tokenized_treasuries",
                    "is_demo": True,
                    "summary": "DEMO / SYNTHETIC RWA profile",
                },
                "hits": [],
            },
            source="DEMO / SYNTHETIC static provider",
            is_demo=True,
        )

    def fetch_intel_events(self, query: str, limit: int = 10) -> ProviderResult:
        return ProviderResult(
            ok=True,
            data={"events": []},
            source="DEMO / SYNTHETIC static provider",
            is_demo=True,
            partial=True,
        )


class FailingProvider:
    """Test double for timeout / rate-limit / error paths."""

    name = "failing"

    def __init__(self, mode: str = "error") -> None:
        self.mode = mode  # error|timeout|rate_limit|empty

    def _fail(self) -> ProviderResult:
        if self.mode == "timeout":
            return ProviderResult(
                ok=False, source=self.name, error="DATA UNAVAILABLE — timeout", timed_out=True
            )
        if self.mode == "rate_limit":
            return ProviderResult(
                ok=False,
                source=self.name,
                error="DATA UNAVAILABLE — rate limited",
                rate_limited=True,
            )
        if self.mode == "empty":
            return ProviderResult(
                ok=False, source=self.name, error="DATA UNAVAILABLE — empty", partial=True
            )
        return ProviderResult(ok=False, source=self.name, error="DATA UNAVAILABLE — provider error")

    def fetch_wallet(self, address: str, chain: str = "ethereum") -> ProviderResult:
        return self._fail()

    def fetch_token(self, token_id_or_symbol: str) -> ProviderResult:
        return self._fail()

    def fetch_project(self, name: str) -> ProviderResult:
        return self._fail()

    def fetch_protocol(self, name: str) -> ProviderResult:
        return self._fail()

    def fetch_rwa(self, name: str) -> ProviderResult:
        return self._fail()

    def fetch_intel_events(self, query: str, limit: int = 10) -> ProviderResult:
        return self._fail()
