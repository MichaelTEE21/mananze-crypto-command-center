"""Tenant-scoped fulfilment strategy model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


FulfilmentStrategyType = Literal[
    "inventory_first",
    "procurement_after_payment",
    "procurement_before_payment",
    "make_to_order",
    "service_delivery",
    "hybrid",
    "custom",
]


FulfilmentStrategyConfirmationStatus = Literal[
    "unconfirmed",
    "partially_confirmed",
    "confirmed",
]


@dataclass(frozen=True)
class FulfilmentStrategy:
    """A business-defined rule describing how fulfilment normally occurs.

    The strategy is tenant-specific business truth. It does not itself
    select suppliers, purchase materials, reserve inventory, or execute
    external actions.
    """

    strategy_id: str
    tenant_id: str
    strategy_type: FulfilmentStrategyType
    name: str
    description: str = ""
    confirmation_status: FulfilmentStrategyConfirmationStatus = "unconfirmed"
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.strategy_id.strip():
            raise ValueError("strategy_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.strategy_type.strip():
            raise ValueError("strategy_type is required")

        if self.strategy_type not in {
            "inventory_first",
            "procurement_after_payment",
            "procurement_before_payment",
            "make_to_order",
            "service_delivery",
            "hybrid",
            "custom",
        }:
            raise ValueError("invalid strategy_type")

        if not self.name.strip():
            raise ValueError("name is required")

        if not self.confirmation_status.strip():
            raise ValueError("confirmation_status is required")

        if self.confirmation_status not in {
            "unconfirmed",
            "partially_confirmed",
            "confirmed",
        }:
            raise ValueError("invalid confirmation_status")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


__all__ = [
    "FulfilmentStrategy",
    "FulfilmentStrategyConfirmationStatus",
    "FulfilmentStrategyType",
]
