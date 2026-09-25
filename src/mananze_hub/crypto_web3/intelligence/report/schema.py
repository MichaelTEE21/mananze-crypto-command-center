"""Intelligence Report schema — entity types, sections, confidence, provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


REPORT_DISCLAIMER = (
    "Research only — not financial advice. MCCC never asks for seed phrases, private keys, "
    "wallet passwords, or recovery phrases. Public blockchain data and labelled DEMO/SYNTHETIC "
    "rows only. Risk language is investigative (Investigate further / Potential risk indicator / "
    "Insufficient data / No conclusion). Never treat DEMO as live."
)


class EntityType(str, Enum):
    PROJECT = "project"
    TOKEN = "token"
    WALLET = "wallet"
    PROTOCOL = "protocol"
    CONTRACT = "contract"
    RWA = "rwa"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"


SUPPORTED_ENTITY_TYPES = frozenset(
    {
        EntityType.PROJECT.value,
        EntityType.TOKEN.value,
        EntityType.WALLET.value,
        EntityType.PROTOCOL.value,
        EntityType.CONTRACT.value,
        EntityType.RWA.value,
    }
)


class DataQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DataMode(str, Enum):
    LIVE = "LIVE"
    DEMO = "DEMO"
    MIXED = "MIXED"
    UNAVAILABLE = "DATA_UNAVAILABLE"


class VerificationLevel(str, Enum):
    VERIFIED = "verified"
    ESTIMATED = "estimated"
    USER_PROVIDED = "user_provided"
    UNKNOWN = "unknown"


RISK_LANGUAGE = (
    "Investigate further",
    "Potential risk indicator",
    "Insufficient data",
    "No conclusion",
)


METRIC_EXPLAINERS: dict[str, dict[str, str]] = {
    "tvl": {
        "what": "Total Value Locked — value of assets deposited in a protocol smart contracts (when reported).",
        "why": "Researchers use it as one activity proxy for DeFi protocols.",
        "cannot": "TVL is not revenue, not profit, not safety, and not a buy/sell signal. It can be inflated or stale.",
    },
    "balance": {
        "what": "Public on-chain native token balance for an address when an explorer/RPC responds.",
        "why": "Helps answer what assets appear at this public address.",
        "cannot": "Balance alone does not prove ownership identity, intent, or future activity.",
    },
    "market_cap": {
        "what": "Circulating supply × price from a market data provider (when live).",
        "why": "One size proxy among many research dimensions.",
        "cannot": "Market cap is not fundamental value and DEMO quotes must never be treated as live.",
    },
    "tx_count": {
        "what": "Count of observed public transactions in the available window.",
        "why": "Activity volume hint for research.",
        "cannot": "Counts can be incomplete under rate limits; absence of data is not proof of inactivity.",
    },
    "concentration": {
        "what": "Share of observed holdings/activity concentrated in few tokens or counterparties.",
        "why": "Potential risk indicator for diversification research.",
        "cannot": "Concentration alone yields No conclusion on whether activity is good or bad.",
    },
}


@dataclass
class Provenance:
    source: str
    timestamp: str
    chain: str = "unknown"
    definition: str = ""
    is_live: bool = False
    verification: str = VerificationLevel.UNKNOWN.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Metric:
    key: str
    label: str
    value: Any
    unit: str = ""
    provenance: Optional[Provenance] = None
    unavailable_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.provenance is None:
            d["provenance"] = None
        return d


@dataclass
class RiskFlag:
    code: str
    title: str
    detail: str
    language: str = "Potential risk indicator"  # must be from RISK_LANGUAGE
    severity: str = "info"  # info|warn|investigate

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceRef:
    title: str
    url: str = ""
    source_type: str = "internal"
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeObservation:
    field: str
    previous: Any
    current: Any
    observed_at_previous: str = ""
    observed_at_current: str = ""
    note: str = "Observed difference only — no cause invented."

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BeginnerBlock:
    what_does_this_mean: str
    why_should_i_care: str
    what_to_investigate_next: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceReport:
    """Full 10-section intelligence report for a supported entity."""

    report_id: str
    entity_type: str
    query: str
    display_name: str
    chain: str = "unknown"
    data_mode: str = DataMode.UNAVAILABLE.value
    confidence: str = DataQuality.LOW.value
    confidence_reasons: list[str] = field(default_factory=list)

    executive_summary: str = ""
    what_is_this_plain: str = ""
    what_is_this_advanced: str = ""
    on_chain_metrics: list[Metric] = field(default_factory=list)
    wallet_intelligence: dict[str, Any] = field(default_factory=dict)
    token_intelligence: dict[str, Any] = field(default_factory=dict)
    risk_flags: list[RiskFlag] = field(default_factory=list)
    changes: list[ChangeObservation] = field(default_factory=list)
    beginner: Optional[BeginnerBlock] = None
    sources: list[SourceRef] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_demo: bool = False
    unsupported_reason: str = ""
    created_at: str = ""
    raw_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "entity_type": self.entity_type,
            "query": self.query,
            "display_name": self.display_name,
            "chain": self.chain,
            "data_mode": self.data_mode,
            "confidence": self.confidence,
            "confidence_reasons": list(self.confidence_reasons),
            "executive_summary": self.executive_summary,
            "what_is_this_plain": self.what_is_this_plain,
            "what_is_this_advanced": self.what_is_this_advanced,
            "on_chain_metrics": [m.to_dict() for m in self.on_chain_metrics],
            "wallet_intelligence": dict(self.wallet_intelligence),
            "token_intelligence": dict(self.token_intelligence),
            "risk_flags": [r.to_dict() for r in self.risk_flags],
            "changes": [c.to_dict() for c in self.changes],
            "beginner": self.beginner.to_dict() if self.beginner else None,
            "sources": [s.to_dict() for s in self.sources],
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "is_demo": self.is_demo,
            "unsupported_reason": self.unsupported_reason,
            "created_at": self.created_at,
            "raw_snapshot": dict(self.raw_snapshot),
            "disclaimer": REPORT_DISCLAIMER,
        }

    def context_for_assistant(self, *, max_chars: int = 1800) -> str:
        """Compact labelled context for AI — never invent beyond this block."""
        lines = [
            f"[FACT] Intelligence Report context for {self.entity_type}: {self.display_name}",
            f"[FACT] query={self.query} chain={self.chain} mode={self.data_mode} confidence={self.confidence}",
            f"[DATA] executive_summary: {self.executive_summary}",
            f"[DATA] confidence_reasons: {'; '.join(self.confidence_reasons) or 'n/a'}",
        ]
        if self.is_demo or self.data_mode == DataMode.DEMO.value:
            lines.append("[FACT] This report includes DEMO/SYNTHETIC labelled data — never present as live.")
        if self.data_mode == DataMode.UNAVAILABLE.value:
            lines.append("[DATA] On-chain/live fields: DATA UNAVAILABLE — do not invent numbers.")
        for m in self.on_chain_metrics[:6]:
            if m.unavailable_reason:
                lines.append(f"[DATA] {m.label}: DATA UNAVAILABLE ({m.unavailable_reason})")
            else:
                live = "LIVE" if (m.provenance and m.provenance.is_live) else "DEMO/LOCAL"
                lines.append(f"[DATA] {m.label}={m.value}{(' ' + m.unit) if m.unit else ''} [{live}]")
        for rf in self.risk_flags[:4]:
            lines.append(f"[ANALYSIS] {rf.language}: {rf.title} — {rf.detail}")
        if self.beginner:
            lines.append(f"[ANALYSIS] beginner_next: {self.beginner.what_to_investigate_next}")
        text = "\n".join(lines)
        return text[:max_chars]
