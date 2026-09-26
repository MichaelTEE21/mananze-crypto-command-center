"""End-to-end quote preparation pipeline for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.inventory_fulfilment import InventoryFulfilmentAssessment
from mananze_os.pricing_resolution import PricingResolution
from mananze_os.quote import Quote
from mananze_os.quote_builder import QuoteBuildResult, build_quote
from mananze_os.quote_readiness import QuoteReadinessAssessment
from mananze_os.requirement_validation import RequirementValidationResult


@dataclass(frozen=True)
class QuotePipelineResult:
    """Complete commercial preparation result.

    This pipeline prepares a quote but does not send, accept, execute,
    procure, reserve inventory, or trigger payment actions.
    """

    build: QuoteBuildResult
    readiness: QuoteReadinessAssessment | None

    @property
    def ready_to_send(self) -> bool:
        return (
            self.build.ready
            and self.readiness is not None
            and self.readiness.can_quote_automatically
        )

    @property
    def must_freeze(self) -> bool:
        return not self.ready_to_send

    @property
    def quote(self) -> Quote | None:
        return self.build.quote


def prepare_quote(
    *,
    quote_id: str,
    tenant_id: str,
    customer_reference: str,
    currency: str,
    validation: RequirementValidationResult,
    pricing_resolutions: list[PricingResolution],
    fulfilment: InventoryFulfilmentAssessment | None = None,
    evidence_ids: tuple[str, ...] = (),
) -> QuotePipelineResult:
    """Prepare a quote through validation, pricing, assembly and readiness.

    Any unresolved pricing is blocked by Quote Builder.
    Any validation exception is blocked by Quote Readiness.
    """

    if validation.tenant_id != tenant_id:
        raise ValueError("validation tenant does not match quote tenant")

    if validation.requirement_id.strip() == "":
        raise ValueError("validation requirement_id is required")

    build = build_quote(
        quote_id=quote_id,
        tenant_id=tenant_id,
        customer_reference=customer_reference,
        currency=currency,
        resolutions=pricing_resolutions,
        evidence_ids=evidence_ids,
    )

    if not build.ready:
        return QuotePipelineResult(
            build=build,
            readiness=None,
        )

    from mananze_os.quote_readiness import assess_quote_readiness

    readiness = assess_quote_readiness(
        validation=validation,
        fulfilment=fulfilment,
    )

    return QuotePipelineResult(
        build=build,
        readiness=readiness,
    )


__all__ = [
    "QuotePipelineResult",
    "prepare_quote",
]
