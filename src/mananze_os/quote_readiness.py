"""Quote readiness assessment for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.inventory_fulfilment import InventoryFulfilmentAssessment
from mananze_os.quote_decision import QuoteDecisionResult, decide_quote
from mananze_os.requirement_validation import RequirementValidationResult


@dataclass(frozen=True)
class QuoteReadinessAssessment:
    """Combined requirement, quote-decision and fulfilment readiness."""

    decision: QuoteDecisionResult
    validation: RequirementValidationResult
    fulfilment: InventoryFulfilmentAssessment | None

    @property
    def can_quote_automatically(self) -> bool:
        return (
            self.decision.can_proceed_automatically
            and self.validation.passed
        )

    @property
    def must_freeze(self) -> bool:
        return not self.can_quote_automatically


def assess_quote_readiness(
    *,
    validation: RequirementValidationResult,
    fulfilment: InventoryFulfilmentAssessment | None = None,
) -> QuoteReadinessAssessment:
    """Connect requirement validation to the quote decision gate."""

    has_conflict = any(
        finding.disposition == "conflict"
        for finding in validation.findings
    )

    insufficient_evidence = any(
        finding.disposition == "insufficient_evidence"
        for finding in validation.findings
    )

    requires_review = any(
        finding.disposition == "review_required"
        for finding in validation.findings
    )

    decision = decide_quote(
        evidence_sufficient=not insufficient_evidence,
        has_conflict=has_conflict,
        requires_review=requires_review,
    )

    return QuoteReadinessAssessment(
        decision=decision,
        validation=validation,
        fulfilment=fulfilment,
    )


__all__ = [
    "QuoteReadinessAssessment",
    "assess_quote_readiness",
]
