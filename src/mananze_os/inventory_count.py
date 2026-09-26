"""Tenant-scoped physical inventory count model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryCount:
    """A physical count of an inventory item.

    A count records observed physical stock. It does not automatically
    modify inventory, approve an adjustment, or decide which quantity
    is authoritative.
    """

    count_id: str
    tenant_id: str
    item_id: str
    recorded_quantity: float
    counted_quantity: float
    unit: str
    evidence_ids: tuple[str, ...] = ()

    @property
    def variance(self) -> float:
        """Difference between physical and recorded quantity."""
        return self.counted_quantity - self.recorded_quantity

    def __post_init__(self) -> None:
        if not self.count_id.strip():
            raise ValueError("count_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if self.recorded_quantity < 0:
            raise ValueError("recorded_quantity cannot be negative")
        if self.counted_quantity < 0:
            raise ValueError("counted_quantity cannot be negative")
        if not self.unit.strip():
            raise ValueError("unit is required")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


__all__ = ["InventoryCount"]
