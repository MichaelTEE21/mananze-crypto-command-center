"""Customer quote decision domain model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


CustomerDecision = Literal["accepted", "declined"]


@dataclass(frozen=True)
class CustomerQuoteDecision:
    """Immutable customer decision on a specific quote.

    This records the customer's commercial decision.
    It does not trigger payment, procurement, production, or execution.
    """

    decision_id: str
    tenant_id: str
    quote_id: str
    decision: CustomerDecision
    decided_at: datetime
    evidence_ids: tuple[str, ...] = ()
    customer_reference: str = ""

    def __post_init__(self) -> None:
        if not self.decision_id.strip():
            raise ValueError("decision_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.quote_id.strip():
            raise ValueError("quote_id is required")

        if self.decision not in {"accepted", "declined"}:
            raise ValueError("invalid customer decision")

        if self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware")

        if self.decided_at > datetime.now(timezone.utc):
            raise ValueError("decided_at cannot be in the future")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")

    @property
    def accepted(self) -> bool:
        return self.decision == "accepted"

    @property
    def declined(self) -> bool:
        return self.decision == "declined"


__all__ = [
    "CustomerDecision",
    "CustomerQuoteDecision",
]
