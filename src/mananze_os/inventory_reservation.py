"""Tenant-scoped inventory reservation model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


InventoryReservationStatus = Literal[
    "reserved",
    "released",
    "consumed",
    "cancelled",
]


@dataclass(frozen=True)
class InventoryReservation:
    """A commitment of existing inventory to a business job.

    A reservation does not physically consume stock. It records that
    available inventory has been committed to a specific job or work
    reference. Physical consumption is represented separately by an
    inventory movement.
    """

    reservation_id: str
    tenant_id: str
    item_id: str
    quantity: float
    unit: str
    job_id: str
    status: InventoryReservationStatus = "reserved"

    def __post_init__(self) -> None:
        if not self.reservation_id.strip():
            raise ValueError("reservation_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        if not self.unit.strip():
            raise ValueError("unit is required")
        if not self.job_id.strip():
            raise ValueError("job_id is required")
        if not self.status.strip():
            raise ValueError("status is required")

        if self.status not in {
            "reserved",
            "released",
            "consumed",
            "cancelled",
        }:
            raise ValueError("invalid status")


__all__ = [
    "InventoryReservation",
    "InventoryReservationStatus",
]
