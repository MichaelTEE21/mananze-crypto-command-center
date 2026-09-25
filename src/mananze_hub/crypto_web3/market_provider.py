"""Market data provider abstraction + CoinGecko implementation with TTL cache.

Never silently fake live data — always return is_live flag.
DEMO fallback is explicitly labelled.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional, Protocol, runtime_checkable

import requests

from mccc.demo_data import DEMO_PRICES
from mccc.market import DEFAULT_IDS, COINGECKO_URL, fetch_prices as _legacy_fetch_prices

GLOBAL_URL = "https://api.coingecko.com/api/v3/global"


@runtime_checkable
class MarketProvider(Protocol):
    def get_prices(
        self,
        ids: str = ...,
        vs_currency: str = ...,
    ) -> tuple[list[dict[str, Any]], str, bool]:
        """Returns (rows, source_label, is_live)."""
        ...

    def get_overview(self) -> tuple[dict[str, Any], str, bool]:
        """Global market overview (btc/eth dominance, total mcap when available)."""
        ...

    def price_map(self, ids: str = ..., vs_currency: str = ...) -> tuple[dict[str, float], str, bool]:
        """Symbol → USD price map."""
        ...


class _TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str, ttl: float) -> Optional[Any]:
        hit = self._store.get(key)
        if not hit:
            return None
        ts, value = hit
        if time.time() - ts > ttl:
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)

    def clear(self) -> None:
        self._store.clear()


_CACHE = _TTLCache()


class CoinGeckoProvider:
    """Wraps CoinGecko public API; falls back to labelled DEMO data."""

    def __init__(self, ttl_seconds: float = 60.0, timeout: float = 8.0) -> None:
        self.ttl_seconds = ttl_seconds
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        api_key = os.environ.get("COINGECKO_API_KEY", "").strip()
        if api_key:
            headers["x-cg-demo-api-key"] = api_key
        return headers

    def get_prices(
        self,
        ids: str = DEFAULT_IDS,
        vs_currency: str = "usd",
    ) -> tuple[list[dict[str, Any]], str, bool]:
        cache_key = f"prices:{ids}:{vs_currency}"
        cached = _CACHE.get(cache_key, self.ttl_seconds)
        if cached is not None:
            return cached
        # Reuse legacy fetcher for consistent shape
        result = _legacy_fetch_prices(ids=ids, vs_currency=vs_currency, timeout=self.timeout)
        _CACHE.set(cache_key, result)
        return result

    def price_map(
        self,
        ids: str = DEFAULT_IDS,
        vs_currency: str = "usd",
    ) -> tuple[dict[str, float], str, bool]:
        rows, source, is_live = self.get_prices(ids=ids, vs_currency=vs_currency)
        mapping: dict[str, float] = {}
        for row in rows:
            sym = (row.get("symbol") or "").upper()
            px = row.get("current_price")
            if sym and px is not None:
                try:
                    mapping[sym] = float(px)
                except (TypeError, ValueError):
                    continue
        return mapping, source, is_live

    def get_overview(self) -> tuple[dict[str, Any], str, bool]:
        cache_key = "overview:global"
        cached = _CACHE.get(cache_key, self.ttl_seconds)
        if cached is not None:
            return cached

        # Start with coin prices for btc/eth/sol
        rows, price_source, prices_live = self.get_prices(
            ids="bitcoin,ethereum,solana",
            vs_currency="usd",
        )
        by_id = {r.get("id"): r for r in rows}
        overview: dict[str, Any] = {
            "btc": by_id.get("bitcoin") or by_id.get("demo-bitcoin"),
            "eth": by_id.get("ethereum") or by_id.get("demo-ethereum"),
            "sol": by_id.get("solana") or by_id.get("demo-solana"),
            "total_market_cap_usd": None,
            "btc_dominance": None,
            "eth_dominance": None,
        }

        if not prices_live:
            # DEMO overview — never claim live
            demo = {
                "btc": next((r for r in DEMO_PRICES if "bitcoin" in str(r.get("id"))), DEMO_PRICES[0]),
                "eth": next((r for r in DEMO_PRICES if "ethereum" in str(r.get("id"))), DEMO_PRICES[1]),
                "sol": next((r for r in DEMO_PRICES if "solana" in str(r.get("id"))), DEMO_PRICES[2]),
                "total_market_cap_usd": None,
                "btc_dominance": None,
                "eth_dominance": None,
            }
            result = (demo, "DEMO fallback — CoinGecko unreachable or rate-limited", False)
            _CACHE.set(cache_key, result)
            return result

        try:
            resp = requests.get(GLOBAL_URL, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json().get("data") or {}
            mcap = (data.get("total_market_cap") or {}).get("usd")
            overview["total_market_cap_usd"] = mcap
            overview["btc_dominance"] = data.get("market_cap_percentage", {}).get("btc")
            overview["eth_dominance"] = data.get("market_cap_percentage", {}).get("eth")
            result = (
                overview,
                f"{price_source}; CoinGecko /global",
                True,
            )
            _CACHE.set(cache_key, result)
            return result
        except Exception:
            # Prices may still be live; global endpoint failed — still report prices live but note gap
            result = (
                overview,
                f"{price_source}; global overview unavailable",
                prices_live,
            )
            _CACHE.set(cache_key, result)
            return result


def get_default_provider() -> CoinGeckoProvider:
    return CoinGeckoProvider()


def clear_market_cache() -> None:
    _CACHE.clear()
