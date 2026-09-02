"""Explorer provider interface + registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

DATA_UNAVAILABLE = "DATA UNAVAILABLE"


class ExplorerStatus(str, Enum):
    VERIFIED = "VERIFIED"  # sourced from live provider
    CALCULATED = "CALCULATED"  # derived from retrieved fields
    INFERENCE = "INFERENCE"  # labelled opinion / heuristic only
    UNAVAILABLE = "UNAVAILABLE"
    DEMO = "DEMO"


@dataclass
class ExplorerResult:
    chain: str
    kind: str  # address | tx
    query: str
    status: ExplorerStatus
    source: str
    summary: str
    fields: dict[str, Any] = field(default_factory=dict)
    label: str = ""  # VERIFIED | CALCULATED | INFERENCE | UNAVAILABLE | DEMO

    def as_dict(self) -> dict[str, Any]:
        return {
            "chain": self.chain,
            "kind": self.kind,
            "query": self.query,
            "status": self.status.value,
            "label": self.label or self.status.value,
            "source": self.source,
            "summary": self.summary,
            "fields": dict(self.fields),
        }


class ExplorerProvider(ABC):
    chain: str
    display_name: str

    @abstractmethod
    def available(self) -> bool:
        """True when this provider can attempt a live/demo lookup."""

    @abstractmethod
    def lookup_address(self, address: str) -> ExplorerResult:
        ...

    @abstractmethod
    def lookup_tx(self, tx_hash: str) -> ExplorerResult:
        ...


_REGISTRY: dict[str, ExplorerProvider] = {}


def register_provider(provider: ExplorerProvider) -> None:
    _REGISTRY[provider.chain.lower()] = provider


def list_providers() -> list[ExplorerProvider]:
    _ensure_builtin()
    return list(_REGISTRY.values())


def available_chains() -> list[str]:
    return [p.chain for p in list_providers() if p.available()]


def get_provider(chain: str) -> Optional[ExplorerProvider]:
    _ensure_builtin()
    return _REGISTRY.get((chain or "").strip().lower())


def lookup_address(chain: str, address: str) -> ExplorerResult:
    provider = get_provider(chain)
    if not provider or not provider.available():
        return ExplorerResult(
            chain=(chain or "").lower() or "unknown",
            kind="address",
            query=address or "",
            status=ExplorerStatus.UNAVAILABLE,
            source="none",
            summary=DATA_UNAVAILABLE,
            label="UNAVAILABLE",
            fields={"reason": "No explorer provider for this chain"},
        )
    return provider.lookup_address(address)


def lookup_tx(chain: str, tx_hash: str) -> ExplorerResult:
    provider = get_provider(chain)
    if not provider or not provider.available():
        return ExplorerResult(
            chain=(chain or "").lower() or "unknown",
            kind="tx",
            query=tx_hash or "",
            status=ExplorerStatus.UNAVAILABLE,
            source="none",
            summary=DATA_UNAVAILABLE,
            label="UNAVAILABLE",
            fields={"reason": "No explorer provider for this chain"},
        )
    return provider.lookup_tx(tx_hash)


_LOADED = False


def _ensure_builtin() -> None:
    global _LOADED
    if _LOADED:
        return
    from mccc.explorers import bitcoin, ethereum, solana  # noqa: F401

    ethereum.register()
    bitcoin.register()
    solana.register()
    _LOADED = True
