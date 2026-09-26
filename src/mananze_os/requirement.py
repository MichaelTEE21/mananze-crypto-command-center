"""Tenant-scoped requirement domain model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


RequirementConfirmationStatus = Literal[
    "unconfirmed",
    "partially_confirmed",
    "confirmed",
]


@dataclass(frozen=True)
class Requirement:
    """Immutable business requirement derived from evidence.

    This model represents what a job requires. It does not perform
    calculation, quoting, procurement, inventory allocation, or execution.
    """

    requirement_id: str
    tenant_id: str
    product_or_material: str
    dimensions: str = ""
    quantity: float = 1
    specification: str = ""
    edging: str = ""
    backer: str = ""
    finish: str = ""
    evidence_ids: tuple[str, ...] = ()
    confirmation_status: RequirementConfirmationStatus = "unconfirmed"

    def __post_init__(self) -> None:
        if not self.requirement_id.strip():
            raise ValueError("requirement_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.product_or_material.strip():
            raise ValueError("product_or_material is required")
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
    "Requirement",
    "RequirementConfirmationStatus",
]
