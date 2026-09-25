"""Market data via CoinGecko public API with DEMO fallback."""
from __future__ import annotations

import os
from typing import Any, Optional

import requests

from mccc.demo_data import DEMO_PRICES

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
DEFAULT_IDS = "bitcoin,ethereum,solana,usd-coin,ripple,cardano"


def fetch_prices(
    ids: str = DEFAULT_IDS,
    vs_currency: str = "usd",
    timeout: float = 8.0,
) -> tuple[list[dict[str, Any]], str, bool]:
    """
    Returns (rows, source_label, is_live).
    On failure returns DEMO_PRICES with clear DEMO labelling.
    """
    headers = {"Accept": "application/json"}
    api_key = os.environ.get("COINGECKO_API_KEY", "").strip()
    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    params = {
        "vs_currency": vs_currency,
        "ids": ids,
        "order": "market_cap_desc",
        "per_page": 25,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    try:
        resp = requests.get(COINGECKO_URL, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or not data:
            raise ValueError("empty response")
        rows = []
        for item in data:
            rows.append(
                {
                    "id": item.get("id"),
                    "symbol": (item.get("symbol") or "").upper(),
                    "name": item.get("name"),
                    "current_price": item.get("current_price"),
                    "price_change_percentage_24h": item.get("price_change_percentage_24h"),
                    "market_cap": item.get("market_cap"),
                }
            )
        return rows, "CoinGecko public API (api.coingecko.com)", True
    except Exception:
        return list(DEMO_PRICES), "DEMO fallback — CoinGecko unreachable or rate-limited", False
