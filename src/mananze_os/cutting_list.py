"""Authoritative cutting-list item model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CuttingListConfirmationStatus = Literal[
    "unconfirmed",
    "partially_confirmed",
    "confirmed",
]


@dataclass(frozen=True)
class CuttingListItem:
    """One item exactly as supplied by the business cutting list.

    Mananze preserves the supplied dimensions and specifications.
    This model does not redesign, recalculate, or judge whether
    the supplied dimensions are correct.
    """

    item_id: str
    tenant_id: str
    material: str
    dimensions: str
    quantity: float = 1
    thickness: str = ""
    edging: str = ""
    backer: str = ""
    finish: str = ""
    evidence_ids: tuple[str, ...] = ()
    confirmation_status: CuttingListConfirmationStatus = "unconfirmed"

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.material.strip():
            raise ValueError("material is required")
        if not self.dimensions.strip():
            raise ValueError("dimensions are required")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
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
    "CuttingListConfirmationStatus",
    "CuttingListItem",
]
