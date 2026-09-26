"""Tenant-scoped quote decision and exception model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


QuoteDecision = Literal[
    "automatic",
    "freeze_and_notify",
]

QuoteDecisionReason = Literal[
    "ready",
    "review_required",
    "conflict",
    "insufficient_evidence",
]


@dataclass(frozen=True)
class QuoteDecisionResult:
    """Decision gate for whether a quote may proceed automatically.

    This model does not calculate prices, send quotes, approve payments,
    or execute external actions. It only determines whether the quote
    workflow may continue or must freeze for human resolution.
    """

    decision: QuoteDecision
    reason: QuoteDecisionReason
    explanation: str

    @property
    def can_proceed_automatically(self) -> bool:
        return self.decision == "automatic"

    @property
    def must_freeze(self) -> bool:
        return self.decision == "freeze_and_notify"

    def __post_init__(self) -> None:
        if not self.decision.strip():
            raise ValueError("decision is required")

        if self.decision not in {
            "automatic",
            "freeze_and_notify",
        }:
            raise ValueError("invalid decision")

        if not self.reason.strip():
            raise ValueError("reason is required")

        if self.reason not in {
            "ready",
            "review_required",
            "conflict",
            "insufficient_evidence",
        }:
            raise ValueError("invalid reason")

        if not self.explanation.strip():
            raise ValueError("explanation is required")


def decide_quote(
    *,
    evidence_sufficient: bool,
    has_conflict: bool,
    requires_review: bool,
) -> QuoteDecisionResult:
    """Determine whether a quote may proceed automatically.

    Decision order deliberately treats uncertainty and conflict as
    blocking conditions. Mananze never guesses past an unresolved
    business truth or evidence problem.
    """

    if has_conflict:
        return QuoteDecisionResult(
            decision="freeze_and_notify",
            reason="conflict",
            explanation="Conflicting business information must be resolved.",
        )

    if not evidence_sufficient:
        return QuoteDecisionResult(
            decision="freeze_and_notify",
            reason="insufficient_evidence",
            explanation="There is not enough reliable evidence to quote safely.",
        )

    if requires_review:
        return QuoteDecisionResult(
            decision="freeze_and_notify",
            reason="review_required",
            explanation="The quote requires human resolution before it can proceed.",
        )

    return QuoteDecisionResult(
        decision="automatic",
        reason="ready",
        explanation="The quote has sufficient evidence and no blocking exception.",
    )


__all__ = [
    "QuoteDecision",
    "QuoteDecisionReason",
    "QuoteDecisionResult",
    "decide_quote",
]
