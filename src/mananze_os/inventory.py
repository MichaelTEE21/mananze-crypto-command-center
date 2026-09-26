"""Tenant-scoped inventory domain models for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryItem:
    """A business-defined item that can be held as stock.

    This model records inventory identity and current on-hand quantity.
    It does not allocate, consume, procure, forecast, or determine
    reorder levels.
    """

    item_id: str
    tenant_id: str
    name: str
    unit: str
    quantity_on_hand: float = 0

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.unit.strip():
            raise ValueError("unit is required")
        if self.quantity_on_hand < 0:
            raise ValueError("quantity_on_hand cannot be negative")


__all__ = ["InventoryItem"]
