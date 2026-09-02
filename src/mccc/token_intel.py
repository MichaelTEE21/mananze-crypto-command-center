"""Token Intelligence foundation — market fields from providers; never invent tokenomics.

Holders / locks / vesting: schema + UNAVAILABLE until Phase 2 data sources.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


DATA_UNAVAILABLE = "DATA UNAVAILABLE"


@dataclass
class FieldProvenance:
    source: str
    last_updated: str
    data_quality: str  # FACT | VERIFIED | ANALYSIS | ESTIMATE | UNVERIFIED | UNKNOWN | UNAVAILABLE
    is_live: bool = False
    is_demo: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TokenMarketSnapshot:
    token_id: str
    symbol: str = ""
    name: str = ""
    price_usd: Any = None
    market_cap_usd: Any = None
    fdv_usd: Any = None
    volume_24h_usd: Any = None
    circulating_supply: Any = None
    total_supply: Any = None
    max_supply: Any = None
    # Phase 2 placeholders — never invent
    holders_count: Any = None
    holders_status: str = DATA_UNAVAILABLE
    tokenomics_status: str = DATA_UNAVAILABLE
    locks_status: str = DATA_UNAVAILABLE
    vesting_status: str = DATA_UNAVAILABLE
    provenance: Optional[FieldProvenance] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _aliases(qid: str) -> str:
    aliases = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana",
        "usdc": "usd-coin",
        "usdt": "tether",
        "bitcoin": "bitcoin",
        "ethereum": "ethereum",
        "solana": "solana",
    }
    key = (qid or "").strip().lower().lstrip("$")
    return aliases.get(key, key)


def build_token_market_snapshot(token_query: str) -> TokenMarketSnapshot:
    """Fetch market section via market_provider. Supply only when present in provider row."""
    tid = _aliases(token_query)
    notes: list[str] = [
        "Holders / tokenomics / locks / vesting: DATA UNAVAILABLE until Phase 2 sourced pipelines.",
        "Not financial advice — research only.",
    ]
    try:
        from mccc.market_provider import get_default_provider

        provider = get_default_provider()
        rows, source, is_live = provider.get_prices(ids=tid)
    except Exception as exc:
        return TokenMarketSnapshot(
            token_id=tid,
            provenance=FieldProvenance(
                source=f"market_provider error: {exc}",
                last_updated=_now_iso(),
                data_quality="UNAVAILABLE",
                is_live=False,
                is_demo=True,
            ),
            notes=notes + [f"Market fetch failed: {exc}"],
        )

    if not rows:
        return TokenMarketSnapshot(
            token_id=tid,
            provenance=FieldProvenance(
                source=source or "market_provider",
                last_updated=_now_iso(),
                data_quality="UNAVAILABLE",
                is_live=False,
                is_demo=not is_live,
            ),
            notes=notes + ["No market rows returned — DATA UNAVAILABLE."],
        )

    row = rows[0]
    # CoinGecko rows may include market_cap, total_volume, circulating_supply, total_supply, max_supply, fully_diluted_valuation
    quality = "FACT" if is_live else "UNVERIFIED"
    snap = TokenMarketSnapshot(
        token_id=str(row.get("id") or tid),
        symbol=str(row.get("symbol") or "").upper(),
        name=str(row.get("name") or ""),
        price_usd=row.get("current_price"),
        market_cap_usd=row.get("market_cap"),
        fdv_usd=row.get("fully_diluted_valuation"),
        volume_24h_usd=row.get("total_volume"),
        circulating_supply=row.get("circulating_supply"),
        total_supply=row.get("total_supply"),
        max_supply=row.get("max_supply"),
        holders_count=None,
        holders_status=DATA_UNAVAILABLE,
        tokenomics_status=DATA_UNAVAILABLE,
        locks_status=DATA_UNAVAILABLE,
        vesting_status=DATA_UNAVAILABLE,
        provenance=FieldProvenance(
            source=source,
            last_updated=_now_iso(),
            data_quality=quality if is_live else "UNVERIFIED",
            is_live=is_live,
            is_demo=not is_live,
        ),
        notes=notes,
    )
    # If supply fields absent, leave None — UI shows UNAVAILABLE (never invent)
    if snap.circulating_supply is None and snap.total_supply is None and snap.max_supply is None:
        snap.notes.append("Supply fields not present in provider response — not invented.")
    if snap.fdv_usd is None:
        snap.notes.append("FDV not present in provider response — DATA UNAVAILABLE (not invented).")
    return snap


def format_money(value: Any) -> str:
    if value is None:
        return DATA_UNAVAILABLE
    try:
        v = float(value)
    except (TypeError, ValueError):
        return DATA_UNAVAILABLE
    if v >= 1e12:
        return f"${v / 1e12:.2f}T"
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.2f}M"
    if v >= 1:
        return f"${v:,.2f}"
    return f"${v:.6g}"
