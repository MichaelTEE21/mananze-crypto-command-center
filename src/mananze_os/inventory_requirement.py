"""Tenant-scoped inventory requirement and shortage calculation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mananze_os.inventory_availability import InventoryAvailability


InventoryRequirementStatus = Literal[
    "satisfied",
    "shortage",
]


@dataclass(frozen=True)
class InventoryRequirementResult:
    """Comparison between required quantity and available inventory."""

    requirement_id: str
    tenant_id: str
    item_id: str
    unit: str
    quantity_required: float
    quantity_available: float
    shortage_quantity: float
    status: InventoryRequirementStatus

    @property
    def satisfied(self) -> bool:
        """Whether available stock satisfies the requirement."""
        return self.status == "satisfied"


def assess_inventory_requirement(
    requirement_id: str,
    quantity_required: float,
    availability: InventoryAvailability,
) -> InventoryRequirementResult:
    """Assess whether available inventory satisfies a requirement.

    This function does not reserve, consume, procure, or mutate stock.
    """

    if not requirement_id.strip():
        raise ValueError("requirement_id is required")

    if quantity_required <= 0:
        raise ValueError("quantity_required must be greater than zero")

    if availability.quantity_available >= quantity_required:
        shortage_quantity = 0.0
        status: InventoryRequirementStatus = "satisfied"
    else:
        shortage_quantity = quantity_required - availability.quantity_available
        status = "shortage"

    return InventoryRequirementResult(
        requirement_id=requirement_id,
        tenant_id=availability.tenant_id,
        item_id=availability.item_id,
        unit=availability.unit,
        quantity_required=quantity_required,
        quantity_available=availability.quantity_available,
        shortage_quantity=shortage_quantity,
        status=status,
    )


__all__ = [
    "InventoryRequirementResult",
    "InventoryRequirementStatus",
    "assess_inventory_requirement",
]
