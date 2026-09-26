"""Tenant-scoped pricing resolution for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mananze_os.pricing_rule import PricingRule
from mananze_os.quote import QuoteLine


PricingResolutionStatus = Literal[
    "resolved",
    "no_rule",
    "conflict",
]


@dataclass(frozen=True)
class PricingResolution:
    """Result of resolving a requirement against business pricing rules."""

    status: PricingResolutionStatus
    quote_line: QuoteLine | None = None
    message: str = ""

    @property
    def resolved(self) -> bool:
        return self.status == "resolved"

    @property
    def requires_exception(self) -> bool:
        return self.status != "resolved"

    def __post_init__(self) -> None:
        if self.status not in {
            "resolved",
            "no_rule",
            "conflict",
        }:
            raise ValueError("invalid pricing resolution status")

        if self.status == "resolved" and self.quote_line is None:
            raise ValueError("resolved pricing requires a quote line")

        if self.status != "resolved" and self.quote_line is not None:
            raise ValueError("exception pricing cannot contain a quote line")

        if not self.message.strip():
            raise ValueError("message is required")


def resolve_unit_price(
    *,
    quote_id: str,
    tenant_id: str,
    line_id: str,
    description: str,
    quantity: float,
    unit: str,
    applies_to: str,
    currency: str,
    rules: list[PricingRule],
) -> PricingResolution:
    """Resolve exactly one applicable unit-price rule.

    Only confirmed, effective unit-price rules are eligible.

    Zero matches produce an exception.
    Multiple matches produce an exception.
    Mananze never chooses between conflicting prices.
    """

    if not quote_id.strip():
        raise ValueError("quote_id is required")

    if not tenant_id.strip():
        raise ValueError("tenant_id is required")

    if not line_id.strip():
        raise ValueError("line_id is required")

    if not description.strip():
        raise ValueError("description is required")

    if quantity <= 0:
        raise ValueError("quantity must be greater than zero")

    if not unit.strip():
        raise ValueError("unit is required")

    if not applies_to.strip():
        raise ValueError("applies_to is required")

    if not currency.strip():
        raise ValueError("currency is required")

    applicable = [
        rule
        for rule in rules
        if rule.tenant_id == tenant_id
        and rule.rule_type == "unit_price"
        and rule.applies_to == applies_to
        and rule.currency == currency
        and rule.confirmation_status == "confirmed"
    ]

    if not applicable:
        return PricingResolution(
            status="no_rule",
            message="No confirmed pricing rule matches the requirement.",
        )

    if len(applicable) > 1:
        return PricingResolution(
            status="conflict",
            message="Multiple confirmed pricing rules match the requirement.",
        )

    rule = applicable[0]

    line = QuoteLine(
        line_id=line_id,
        quote_id=quote_id,
        tenant_id=tenant_id,
        description=description,
        line_type="material",
        quantity=quantity,
        unit=unit,
        unit_price=rule.value,
        currency=currency,
        evidence_ids=rule.evidence_ids,
    )

    return PricingResolution(
        status="resolved",
        quote_line=line,
        message="Pricing rule resolved successfully.",
    )


__all__ = [
    "PricingResolution",
    "PricingResolutionStatus",
    "resolve_unit_price",
]
