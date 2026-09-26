"""Tenant-scoped inventory shortage model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


InventoryShortageStatus = Literal[
    "open",
    "resolved",
    "cancelled",
]


@dataclass(frozen=True)
class InventoryShortage:
    """An immutable record of an inventory shortage.

    A shortage records the gap between what a job requires and what is
    currently available. It does not decide how the shortage is resolved.
    """

    shortage_id: str
    tenant_id: str
    job_id: str
    requirement_id: str
    item_id: str
    unit: str
    quantity_required: float
    quantity_available: float
    shortage_quantity: float
    reason: str
    evidence_ids: tuple[str, ...] = ()
    status: InventoryShortageStatus = "open"

    def __post_init__(self) -> None:
        if not self.shortage_id.strip():
            raise ValueError("shortage_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.job_id.strip():
            raise ValueError("job_id is required")
        if not self.requirement_id.strip():
            raise ValueError("requirement_id is required")
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.unit.strip():
            raise ValueError("unit is required")
        if self.quantity_required <= 0:
            raise ValueError("quantity_required must be greater than zero")
        if self.shortage_quantity <= 0:
            raise ValueError("shortage_quantity must be greater than zero")
        if not self.reason.strip():
            raise ValueError("reason is required")
        if not self.status.strip():
            raise ValueError("status is required")

        if self.status not in {
            "open",
            "resolved",
            "cancelled",
        }:
            raise ValueError("invalid status")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


__all__ = [
    "InventoryShortage",
    "InventoryShortageStatus",
]
