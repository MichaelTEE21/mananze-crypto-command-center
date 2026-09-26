"""Inventory-to-fulfilment assessment for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.fulfilment_strategy import FulfilmentStrategy
from mananze_os.inventory import InventoryItem
from mananze_os.inventory_availability import InventoryAvailability
from mananze_os.inventory_requirement import (
    InventoryRequirementResult,
    assess_inventory_requirement,
)
from mananze_os.inventory_reservation import InventoryReservation
from mananze_os.inventory_shortage import InventoryShortage


@dataclass(frozen=True)
class InventoryFulfilmentAssessment:
    """Combined inventory assessment for a business job.

    This composition layer connects existing inventory Legos without
    mutating stock, creating reservations, procuring materials, or
    deciding how a shortage must be resolved.
    """

    job_id: str
    requirement_id: str
    availability: InventoryAvailability
    requirement: InventoryRequirementResult
    strategy: FulfilmentStrategy
    shortage: InventoryShortage | None


def assess_inventory_fulfilment(
    *,
    job_id: str,
    requirement_id: str,
    quantity_required: float,
    item: InventoryItem,
    reservations: list[InventoryReservation],
    strategy: FulfilmentStrategy,
    shortage_reason: str = "Insufficient available inventory",
) -> InventoryFulfilmentAssessment:
    """Connect inventory availability, requirement, shortage and strategy."""

    if not job_id.strip():
        raise ValueError("job_id is required")

    if strategy.tenant_id != item.tenant_id:
        raise ValueError("strategy tenant does not match inventory tenant")

    for reservation in reservations:
        if reservation.tenant_id != item.tenant_id:
            raise ValueError("reservation tenant does not match inventory tenant")

    availability = InventoryAvailability.calculate(
        item,
        reservations,
    )

    requirement = assess_inventory_requirement(
        requirement_id=requirement_id,
        quantity_required=quantity_required,
        availability=availability,
    )

    shortage = None

    if requirement.status == "shortage":
        shortage = InventoryShortage(
            shortage_id=f"shortage:{job_id}:{requirement_id}:{item.item_id}",
            tenant_id=item.tenant_id,
            job_id=job_id,
            requirement_id=requirement_id,
            item_id=item.item_id,
            unit=item.unit,
            quantity_required=requirement.quantity_required,
            quantity_available=requirement.quantity_available,
            shortage_quantity=requirement.shortage_quantity,
            reason=shortage_reason,
        )

    return InventoryFulfilmentAssessment(
        job_id=job_id,
        requirement_id=requirement_id,
        availability=availability,
        requirement=requirement,
        strategy=strategy,
        shortage=shortage,
    )


__all__ = [
    "InventoryFulfilmentAssessment",
    "assess_inventory_fulfilment",
]
