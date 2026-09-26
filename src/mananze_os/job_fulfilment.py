"""Job fulfilment decision for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mananze_os.fulfilment_strategy import FulfilmentStrategy
from mananze_os.job import Job


JobFulfilmentDecisionType = Literal[
    "inventory",
    "procurement",
    "make_to_order",
    "service_delivery",
    "hybrid",
    "custom",
]


@dataclass(frozen=True)
class JobFulfilmentDecision:
    """Resolved next fulfilment path for a job.

    The decision is derived from the tenant's confirmed fulfilment
    strategy. It does not execute the strategy.
    """

    job_id: str
    tenant_id: str
    decision: JobFulfilmentDecisionType
    strategy_id: str
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("job_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if self.decision not in {
            "inventory",
            "procurement",
            "make_to_order",
            "service_delivery",
            "hybrid",
            "custom",
        }:
            raise ValueError("invalid fulfilment decision")

        if not self.strategy_id.strip():
            raise ValueError("strategy_id is required")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


def resolve_job_fulfilment(
    *,
    job: Job,
    strategy: FulfilmentStrategy,
) -> JobFulfilmentDecision:
    """Resolve a job's fulfilment path from its tenant strategy."""

    if job.tenant_id != strategy.tenant_id:
        raise ValueError("job tenant does not match fulfilment strategy tenant")

    if strategy.confirmation_status != "confirmed":
        raise ValueError("fulfilment strategy is not confirmed")

    mapping: dict[str, JobFulfilmentDecisionType] = {
        "inventory_first": "inventory",
        "procurement_after_payment": "procurement",
        "procurement_before_payment": "procurement",
        "make_to_order": "make_to_order",
        "service_delivery": "service_delivery",
        "hybrid": "hybrid",
        "custom": "custom",
    }

    decision = mapping.get(strategy.strategy_type)

    if decision is None:
        raise ValueError("unsupported fulfilment strategy")

    return JobFulfilmentDecision(
        job_id=job.job_id,
        tenant_id=job.tenant_id,
        decision=decision,
        strategy_id=strategy.strategy_id,
        evidence_ids=strategy.evidence_ids,
    )


__all__ = [
    "JobFulfilmentDecision",
    "JobFulfilmentDecisionType",
    "resolve_job_fulfilment",
]
