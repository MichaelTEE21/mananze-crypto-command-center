"""Tenant-scoped inventory movement model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


InventoryMovementType = Literal[
    "receipt",
    "consumption",
    "adjustment",
    "return",
    "damage",
    "correction",
]


@dataclass(frozen=True)
class InventoryMovement:
    """An immutable event describing a change to inventory.

    This model records what happened. It does not itself change stock,
    approve movements, allocate inventory, procure materials, or execute
    external actions.
    """

    movement_id: str
    tenant_id: str
    item_id: str
    movement_type: InventoryMovementType
    quantity: float
    unit: str
    reason: str
    reference: str = ""
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.movement_id.strip():
            raise ValueError("movement_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.movement_type.strip():
            raise ValueError("movement_type is required")
        if self.movement_type not in {
            "receipt",
            "consumption",
            "adjustment",
            "return",
            "damage",
            "correction",
        }:
            raise ValueError("invalid movement_type")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        if not self.unit.strip():
            raise ValueError("unit is required")
        if not self.reason.strip():
            raise ValueError("reason is required")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


__all__ = [
    "InventoryMovement",
    "InventoryMovementType",
]
