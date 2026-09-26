"""Tenant-scoped pricing rules for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal


PricingRuleType = Literal[
    "unit_price",
    "percentage_markup",
    "percentage_discount",
    "fixed_charge",
]


@dataclass(frozen=True)
class PricingRule:
    """A tenant-specific commercial pricing rule.

    Pricing rules are business truth. Mananze does not assume that a
    material, thickness, finish, customer, or service has a universal
    price or classification.
    """

    rule_id: str
    tenant_id: str
    name: str
    rule_type: PricingRuleType
    value: float
    currency: str
    applies_to: str
    evidence_ids: tuple[str, ...] = ()
    effective_from: date | None = None
    effective_until: date | None = None
    confirmation_status: Literal[
        "unconfirmed",
        "partially_confirmed",
        "confirmed",
    ] = "unconfirmed"

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.name.strip():
            raise ValueError("name is required")

        if not self.rule_type.strip():
            raise ValueError("rule_type is required")

        if self.rule_type not in {
            "unit_price",
            "percentage_markup",
            "percentage_discount",
            "fixed_charge",
        }:
            raise ValueError("invalid rule_type")

        if self.value < 0:
            raise ValueError("value cannot be negative")

        if not self.currency.strip():
            raise ValueError("currency is required")

        if not self.applies_to.strip():
            raise ValueError("applies_to is required")

        if self.confirmation_status not in {
            "unconfirmed",
            "partially_confirmed",
            "confirmed",
        }:
            raise ValueError("invalid confirmation_status")

        if (
            self.effective_from is not None
            and self.effective_until is not None
            and self.effective_until < self.effective_from
        ):
            raise ValueError("effective_until cannot be before effective_from")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")

    def is_effective_on(self, when: date) -> bool:
        """Return whether the rule is effective on a given date."""
        if self.effective_from is not None and when < self.effective_from:
            return False

        if self.effective_until is not None and when > self.effective_until:
            return False

        return True


__all__ = [
    "PricingRule",
    "PricingRuleType",
]
