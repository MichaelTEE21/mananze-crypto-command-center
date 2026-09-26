"""Tenant-scoped quote domain models for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


QuoteStatus = Literal[
    "draft",
    "ready",
    "frozen",
    "sent",
    "accepted",
    "declined",
    "expired",
    "cancelled",
]


QuoteLineType = Literal[
    "material",
    "labour",
    "service",
    "other",
]


@dataclass(frozen=True)
class QuoteLine:
    """One priced line in a business quote.

    The line records a supplied/calculated commercial value. It does not
    determine whether the price itself is correct.
    """

    line_id: str
    quote_id: str
    tenant_id: str
    description: str
    line_type: QuoteLineType
    quantity: float
    unit: str
    unit_price: float
    currency: str
    evidence_ids: tuple[str, ...] = ()

    @property
    def line_total(self) -> float:
        """Total value for this quote line."""
        return self.quantity * self.unit_price

    def __post_init__(self) -> None:
        if not self.line_id.strip():
            raise ValueError("line_id is required")

        if not self.quote_id.strip():
            raise ValueError("quote_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.description.strip():
            raise ValueError("description is required")

        if not self.line_type.strip():
            raise ValueError("line_type is required")

        if self.line_type not in {
            "material",
            "labour",
            "service",
            "other",
        }:
            raise ValueError("invalid line_type")

        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")

        if not self.unit.strip():
            raise ValueError("unit is required")

        if self.unit_price < 0:
            raise ValueError("unit_price cannot be negative")

        if not self.currency.strip():
            raise ValueError("currency is required")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


@dataclass(frozen=True)
class Quote:
    """A tenant-scoped commercial quote.

    This model records the commercial result. It does not send the quote,
    accept payment, procure materials, reserve inventory, or execute work.
    """

    quote_id: str
    tenant_id: str
    customer_reference: str
    currency: str
    lines: tuple[QuoteLine, ...] = ()
    status: QuoteStatus = "draft"
    evidence_ids: tuple[str, ...] = ()

    @property
    def subtotal(self) -> float:
        """Sum of all quote line totals."""
        return sum(line.line_total for line in self.lines)

    def __post_init__(self) -> None:
        if not self.quote_id.strip():
            raise ValueError("quote_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.customer_reference.strip():
            raise ValueError("customer_reference is required")

        if not self.currency.strip():
            raise ValueError("currency is required")

        if not self.status.strip():
            raise ValueError("status is required")

        if self.status not in {
            "draft",
            "ready",
            "frozen",
            "sent",
            "accepted",
            "declined",
            "expired",
            "cancelled",
        }:
            raise ValueError("invalid status")

        for line in self.lines:
            if line.quote_id != self.quote_id:
                raise ValueError("quote line quote_id does not match quote")

            if line.tenant_id != self.tenant_id:
                raise ValueError("quote line tenant_id does not match quote")

            if line.currency != self.currency:
                raise ValueError("quote line currency does not match quote")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


__all__ = [
    "Quote",
    "QuoteLine",
    "QuoteLineType",
    "QuoteStatus",
]
