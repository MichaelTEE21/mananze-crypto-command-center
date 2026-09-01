"""Clearly labelled DEMO / EXAMPLE datasets — never presented as live unless fetched."""
from __future__ import annotations

from typing import Any

DEMO_BANNER = "⚠️ DEMO / EXAMPLE DATA — not live market quotes unless source is labelled."

DEMO_PORTFOLIO: list[dict[str, Any]] = [
    {"asset": "DEMO-ETH", "amount": 2.5, "unit_value_usd": 3200.0, "note": "EXAMPLE holding"},
    {"asset": "DEMO-BTC", "amount": 0.15, "unit_value_usd": 62000.0, "note": "EXAMPLE holding"},
    {"asset": "DEMO-SOL", "amount": 40.0, "unit_value_usd": 145.0, "note": "EXAMPLE holding"},
    {"asset": "DEMO-STABLE", "amount": 5000.0, "unit_value_usd": 1.0, "note": "EXAMPLE cash sleeve"},
]

DEMO_PRICES: list[dict[str, Any]] = [
    {"id": "demo-bitcoin", "symbol": "DEMO-BTC", "name": "DEMO Bitcoin", "current_price": 62000.0, "price_change_percentage_24h": 1.2, "market_cap": 1.2e12},
    {"id": "demo-ethereum", "symbol": "DEMO-ETH", "name": "DEMO Ethereum", "current_price": 3200.0, "price_change_percentage_24h": -0.8, "market_cap": 3.8e11},
    {"id": "demo-solana", "symbol": "DEMO-SOL", "name": "DEMO Solana", "current_price": 145.0, "price_change_percentage_24h": 3.4, "market_cap": 6.5e10},
    {"id": "demo-usd-coin", "symbol": "DEMO-USDC", "name": "DEMO USD Coin", "current_price": 1.0, "price_change_percentage_24h": 0.01, "market_cap": 3.0e10},
]

DEMO_PRICE_HISTORY: dict[str, list[dict[str, Any]]] = {
    "DEMO-BTC": [{"day": i, "price": 60000 + i * 200 + (i % 5) * 150} for i in range(30)],
    "DEMO-ETH": [{"day": i, "price": 3000 + i * 12 + (i % 7) * 40} for i in range(30)],
    "DEMO-SOL": [{"day": i, "price": 130 + i * 0.8 + (i % 4) * 2} for i in range(30)],
}

DEMO_WALLET_BALANCES: dict[str, dict[str, Any]] = {
    "0xDEMO000000000000000000000000000000000001": {
        "label": "DEMO Watch Address 1",
        "chain": "ethereum",
        "balances": [
            {"token": "ETH", "amount": 1.234, "usd_value": 3948.8, "source": "DEMO"},
            {"token": "USDC", "amount": 250.0, "usd_value": 250.0, "source": "DEMO"},
        ],
    },
    "0xDEMO000000000000000000000000000000000002": {
        "label": "DEMO Watch Address 2",
        "chain": "ethereum",
        "balances": [
            {"token": "ETH", "amount": 0.05, "usd_value": 160.0, "source": "DEMO"},
        ],
    },
}


def portfolio_summary() -> dict[str, Any]:
    total = sum(r["amount"] * r["unit_value_usd"] for r in DEMO_PORTFOLIO)
    return {
        "total_usd": round(total, 2),
        "positions": len(DEMO_PORTFOLIO),
        "label": "DEMO portfolio summary",
        "source": "DEMO / EXAMPLE — not connected to any exchange",
    }
