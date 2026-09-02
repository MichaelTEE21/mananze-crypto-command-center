"""Market service facade — re-exports market_provider + legacy market helpers."""
from __future__ import annotations

from mccc.market import COINGECKO_URL, DEFAULT_IDS, fetch_prices
from mccc.market_provider import (
    CoinGeckoProvider,
    MarketProvider,
    clear_market_cache,
    get_default_provider,
)

__all__ = [
    "COINGECKO_URL",
    "DEFAULT_IDS",
    "CoinGeckoProvider",
    "MarketProvider",
    "clear_market_cache",
    "fetch_prices",
    "get_default_provider",
]
