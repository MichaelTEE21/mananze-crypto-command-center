"""Provider execution contracts for the Mananze OS.

Providers are adapters behind the centralized execution boundary.
They do not grant authority and must not bypass policy, authorization,
approval, tenant isolation, or economic controls.
"""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderRequest:
    provider_id: str
    tool_id: str
    tenant_id: str
    execution_id: str
    operation: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ProviderResponse:
    provider_id: str
    tool_id: str
    tenant_id: str
    execution_id: str
    success: bool
    output: dict[str, Any]
    error: str | None = None
    usage: dict[str, Any] | None = None
    cost: float = 0.0
    cost_currency: str = "ZAR"


class Provider(Protocol):
    @property
    def provider_id(self) -> str:
        ...

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        ...


__all__ = [
    "Provider",
    "ProviderRequest",
    "ProviderResponse",
]
