"""Tenant-scoped inventory availability calculation for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from mananze_os.inventory import InventoryItem
from mananze_os.inventory_reservation import InventoryReservation


@dataclass(frozen=True)
class InventoryAvailability:
    """Calculated stock position for one inventory item.

    Available quantity is physical stock minus active reservations.
    This model does not mutate inventory or reservations.
    """

    item_id: str
    tenant_id: str
    unit: str
    quantity_on_hand: float
    quantity_reserved: float
    quantity_available: float

    @classmethod
    def calculate(
        cls,
        item: InventoryItem,
        reservations: Iterable[InventoryReservation],
    ) -> "InventoryAvailability":
        quantity_reserved = 0.0

        for reservation in reservations:
            if reservation.tenant_id != item.tenant_id:
                continue

            if reservation.item_id != item.item_id:
                continue

            if reservation.unit != item.unit:
                continue

            if reservation.status != "reserved":
                continue

            quantity_reserved += reservation.quantity

        quantity_available = item.quantity_on_hand - quantity_reserved

        return cls(
            item_id=item.item_id,
            tenant_id=item.tenant_id,
            unit=item.unit,
            quantity_on_hand=item.quantity_on_hand,
            quantity_reserved=quantity_reserved,
            quantity_available=quantity_available,
        )


__all__ = ["InventoryAvailability"]
