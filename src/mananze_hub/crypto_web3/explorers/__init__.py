"""Modular chain explorer providers — wallet + tx lookup.

Only chains with real providers return data; others are UNAVAILABLE.
Never fabricate balances or transactions.
"""
from __future__ import annotations

from mccc.explorers.base import (
    DATA_UNAVAILABLE,
    ExplorerResult,
    ExplorerStatus,
    available_chains,
    get_provider,
    list_providers,
    lookup_address,
    lookup_tx,
)

__all__ = [
    "DATA_UNAVAILABLE",
    "ExplorerResult",
    "ExplorerStatus",
    "available_chains",
    "get_provider",
    "list_providers",
    "lookup_address",
    "lookup_tx",
]
