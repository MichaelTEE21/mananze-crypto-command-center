"""Service facades for MCCC 2.0.

Thin re-exports so callers can use ``mccc.services.market`` / ``mccc.services.ai``
while legacy imports (``from mccc.market_provider import ...``) keep working.
"""
from __future__ import annotations

from mccc.services import ai as ai
from mccc.services import market as market

__all__ = ["ai", "market"]
