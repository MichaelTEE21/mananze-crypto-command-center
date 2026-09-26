"""Job fulfilment lifecycle model for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


JobLifecycleStage = Literal[
    "fulfilment_pending",
    "inventory_pending",
    "procurement_pending",
    "make_to_order_pending",
    "service_delivery_pending",
    "in_progress",
    "qc_pending",
    "delivery_pending",
    "collection_pending",
    "completed",
    "on_hold",
    "cancelled",
]


@dataclass(frozen=True)
class JobLifecycle:
    """Tenant-scoped lifecycle state for a job.

    This model records where a job is in its fulfilment lifecycle.
    It does not execute work, purchase materials, move stock, deliver
    goods, or call external systems.
    """

    job_id: str
    tenant_id: str
    stage: JobLifecycleStage
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("job_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if self.stage not in {
            "fulfilment_pending",
            "inventory_pending",
            "procurement_pending",
            "make_to_order_pending",
            "service_delivery_pending",
            "in_progress",
            "qc_pending",
            "delivery_pending",
            "collection_pending",
            "completed",
            "on_hold",
            "cancelled",
        }:
            raise ValueError("invalid job lifecycle stage")

        for evidence_id in self.evidence_ids:
            if not evidence_id.strip():
                raise ValueError("evidence_ids cannot contain blank values")


def create_job_lifecycle(
    *,
    job_id: str,
    tenant_id: str,
    evidence_ids: tuple[str, ...] = (),
) -> JobLifecycle:
    """Create a new job at the fulfilment-pending stage."""

    return JobLifecycle(
        job_id=job_id,
        tenant_id=tenant_id,
        stage="fulfilment_pending",
        evidence_ids=evidence_ids,
    )


def advance_job_lifecycle(
    *,
    lifecycle: JobLifecycle,
    stage: JobLifecycleStage,
) -> JobLifecycle:
    """Return a new lifecycle state without executing any action."""

    allowed_transitions: dict[JobLifecycleStage, set[JobLifecycleStage]] = {
        "fulfilment_pending": {
            "inventory_pending",
            "procurement_pending",
            "make_to_order_pending",
            "service_delivery_pending",
            "on_hold",
            "cancelled",
        },
        "inventory_pending": {
            "in_progress",
            "on_hold",
            "cancelled",
        },
        "procurement_pending": {
            "in_progress",
            "on_hold",
            "cancelled",
        },
        "make_to_order_pending": {
            "in_progress",
            "on_hold",
            "cancelled",
        },
        "service_delivery_pending": {
            "in_progress",
            "on_hold",
            "cancelled",
        },
        "in_progress": {
            "qc_pending",
            "on_hold",
            "cancelled",
        },
        "qc_pending": {
            "delivery_pending",
            "collection_pending",
            "in_progress",
            "on_hold",
        },
        "delivery_pending": {
            "completed",
            "on_hold",
        },
        "collection_pending": {
            "completed",
            "on_hold",
        },
        "completed": set(),
        "on_hold": {
            "in_progress",
            "cancelled",
        },
        "cancelled": set(),
    }

    if stage not in allowed_transitions[lifecycle.stage]:
        raise ValueError(
            f"invalid lifecycle transition: "
            f"{lifecycle.stage} -> {stage}"
        )

    return JobLifecycle(
        job_id=lifecycle.job_id,
        tenant_id=lifecycle.tenant_id,
        stage=stage,
        evidence_ids=lifecycle.evidence_ids,
    )


__all__ = [
    "JobLifecycle",
    "JobLifecycleStage",
    "advance_job_lifecycle",
    "create_job_lifecycle",
]
