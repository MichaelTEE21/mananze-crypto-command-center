"""Quote assembly for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.pricing_resolution import PricingResolution
from mananze_os.quote import Quote, QuoteStatus


@dataclass(frozen=True)
class QuoteBuildResult:
    """Result of assembling pricing resolutions into a quote."""

    quote: Quote | None
    blocked: bool
    reason: str

    @property
    def ready(self) -> bool:
        return self.quote is not None and not self.blocked


def build_quote(
    *,
    quote_id: str,
    tenant_id: str,
    customer_reference: str,
    currency: str,
    resolutions: list[PricingResolution],
    evidence_ids: tuple[str, ...] = (),
) -> QuoteBuildResult:
    """Build a quote only when every pricing resolution is resolved.

    A single unresolved pricing line blocks the complete quote.
    Mananze never silently omits an unresolved line.
    """

    if not quote_id.strip():
        raise ValueError("quote_id is required")

    if not tenant_id.strip():
        raise ValueError("tenant_id is required")

    if not customer_reference.strip():
        raise ValueError("customer_reference is required")

    if not currency.strip():
        raise ValueError("currency is required")

    for evidence_id in evidence_ids:
        if not evidence_id.strip():
            raise ValueError("evidence_ids cannot contain blank values")

    if not resolutions:
        return QuoteBuildResult(
            quote=None,
            blocked=True,
            reason="No pricing resolutions were supplied.",
        )

    unresolved = [
        resolution
        for resolution in resolutions
        if not resolution.resolved
    ]

    if unresolved:
        reasons = ", ".join(
            resolution.status
            for resolution in unresolved
        )

        return QuoteBuildResult(
            quote=None,
            blocked=True,
            reason=f"Quote blocked by unresolved pricing: {reasons}.",
        )

    lines = tuple(
        resolution.quote_line
        for resolution in resolutions
        if resolution.quote_line is not None
    )

    quote = Quote(
        quote_id=quote_id,
        tenant_id=tenant_id,
        customer_reference=customer_reference,
        currency=currency,
        lines=lines,
        status="ready",
        evidence_ids=evidence_ids,
    )

    return QuoteBuildResult(
        quote=quote,
        blocked=False,
        reason="Quote assembled successfully.",
    )


__all__ = [
    "QuoteBuildResult",
    "build_quote",
]
