"""Job creation domain model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mananze_os.customer_quote_decision import CustomerQuoteDecision
from mananze_os.quote import Quote


JobStatus = Literal[
    "created",
    "in_progress",
    "on_hold",
    "completed",
    "cancelled",
]


@dataclass(frozen=True)
class Job:
    """Tenant-scoped operational job created from an accepted quote.

    Creating a job does not purchase, reserve, manufacture, deliver,
    or otherwise execute fulfilment.
    """

    job_id: str
    tenant_id: str
    quote_id: str
    customer_reference: str
    status: JobStatus = "created"
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("job_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.quote_id.strip():
            raise ValueError("quote_id is required")

        if not self.customer_reference.strip():
            raise ValueError("customer_reference is required")

        if self.status not in {
            "created",
            "in_progress",
            "on_hold",
            "completed",
            "cancelled",
        }:
            raise ValueError("invalid job status")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


def create_job_from_accepted_quote(
    *,
    job_id: str,
    quote: Quote,
    customer_decision: CustomerQuoteDecision,
    evidence_ids: tuple[str, ...] = (),
) -> Job:
    """Create a job only from a matching accepted quote decision."""

    if not job_id.strip():
        raise ValueError("job_id is required")

    if quote.tenant_id != customer_decision.tenant_id:
        raise ValueError("quote tenant does not match customer decision tenant")

    if quote.quote_id != customer_decision.quote_id:
        raise ValueError("quote_id does not match customer decision")

    if not customer_decision.accepted:
        raise ValueError("job can only be created from an accepted quote")

    if quote.status not in {"sent", "accepted"}:
        raise ValueError("quote is not in an acceptable state for job creation")

    for evidence_id in evidence_ids:
        if not evidence_id.strip():
            raise ValueError("evidence_ids cannot contain blank values")

    combined_evidence = tuple(
        dict.fromkeys(
            (
                *quote.evidence_ids,
                *customer_decision.evidence_ids,
                *evidence_ids,
            )
        )
    )

    return Job(
        job_id=job_id,
        tenant_id=quote.tenant_id,
        quote_id=quote.quote_id,
        customer_reference=quote.customer_reference,
        status="created",
        evidence_ids=combined_evidence,
    )


__all__ = [
    "Job",
    "JobStatus",
    "create_job_from_accepted_quote",
]
