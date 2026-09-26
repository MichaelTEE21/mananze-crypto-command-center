"""Payment confirmation evidence for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PaymentConfirmationStatus = Literal[
    "unverified",
    "confirmed",
    "rejected",
    "review_required",
]


@dataclass(frozen=True)
class PaymentConfirmation:
    """Tenant-scoped payment evidence supplied by an authorised source.

    This model does not access banking, accounting, or payment systems.
    It records payment evidence and its verification outcome only.
    """

    confirmation_id: str
    tenant_id: str
    quote_id: str
    status: PaymentConfirmationStatus
    evidence_ids: tuple[str, ...] = ()
    reference: str = ""
    amount: float | None = None
    currency: str = ""
    explanation: str = ""

    def __post_init__(self) -> None:
        if not self.confirmation_id.strip():
            raise ValueError("confirmation_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.quote_id.strip():
            raise ValueError("quote_id is required")
        if self.status not in {
            "unverified",
            "confirmed",
            "rejected",
            "review_required",
        }:
            raise ValueError("invalid payment confirmation status")
        if self.amount is not None and self.amount < 0:
            raise ValueError("amount cannot be negative")
        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")

    @property
    def confirmed(self) -> bool:
        return self.status == "confirmed"

    @property
    def requires_review(self) -> bool:
        return self.status == "review_required"


def assess_payment_confirmation(
    *,
    confirmation_id: str,
    tenant_id: str,
    quote_id: str,
    evidence_ids: tuple[str, ...],
    evidence_sufficient: bool,
    matches_quote: bool,
    explanation: str = "",
    reference: str = "",
    amount: float | None = None,
    currency: str = "",
) -> PaymentConfirmation:
    """Assess payment evidence without accessing a financial system."""

    if not evidence_ids:
        return PaymentConfirmation(
            confirmation_id=confirmation_id,
            tenant_id=tenant_id,
            quote_id=quote_id,
            status="review_required",
            evidence_ids=evidence_ids,
            reference=reference,
            amount=amount,
            currency=currency,
            explanation="Payment evidence is required before fulfilment can proceed.",
        )

    if not evidence_sufficient:
        return PaymentConfirmation(
            confirmation_id=confirmation_id,
            tenant_id=tenant_id,
            quote_id=quote_id,
            status="review_required",
            evidence_ids=evidence_ids,
            reference=reference,
            amount=amount,
            currency=currency,
            explanation="Payment evidence is insufficient to confirm payment safely.",
        )

    if not matches_quote:
        return PaymentConfirmation(
            confirmation_id=confirmation_id,
            tenant_id=tenant_id,
            quote_id=quote_id,
            status="review_required",
            evidence_ids=evidence_ids,
            reference=reference,
            amount=amount,
            currency=currency,
            explanation="Payment evidence does not match the quote.",
        )

    return PaymentConfirmation(
        confirmation_id=confirmation_id,
        tenant_id=tenant_id,
        quote_id=quote_id,
        status="confirmed",
        evidence_ids=evidence_ids,
        reference=reference,
        amount=amount,
        currency=currency,
        explanation=explanation or "Payment evidence was sufficiently matched to the quote.",
    )


__all__ = [
    "PaymentConfirmation",
    "PaymentConfirmationStatus",
    "assess_payment_confirmation",
]
