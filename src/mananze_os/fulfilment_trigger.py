"""Payment-gated job fulfilment transition for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.fulfilment_strategy import FulfilmentStrategy
from mananze_os.job import Job
from mananze_os.job_fulfilment import JobFulfilmentDecision, resolve_job_fulfilment
from mananze_os.job_lifecycle import (
    JobLifecycle,
    advance_job_lifecycle,
    create_job_lifecycle,
)
from mananze_os.payment_confirmation import PaymentConfirmation


@dataclass(frozen=True)
class FulfilmentTriggerResult:
    """Result of evaluating whether a job may enter fulfilment."""

    lifecycle: JobLifecycle
    fulfilment_decision: JobFulfilmentDecision
    triggered: bool
    reason: str

    @property
    def can_proceed(self) -> bool:
        return self.triggered


def trigger_job_fulfilment(
    *,
    job: Job,
    strategy: FulfilmentStrategy,
    payment: PaymentConfirmation | None = None,
) -> FulfilmentTriggerResult:
    """Move a job into its configured fulfilment path when authorised."""

    if job.tenant_id != strategy.tenant_id:
        raise ValueError("job tenant does not match fulfilment strategy tenant")

    if payment is not None:
        if payment.tenant_id != job.tenant_id:
            raise ValueError("payment tenant does not match job tenant")

        if payment.quote_id != job.quote_id:
            raise ValueError("payment quote does not match job quote")

    decision = resolve_job_fulfilment(
        job=job,
        strategy=strategy,
    )

    lifecycle = create_job_lifecycle(
        job_id=job.job_id,
        tenant_id=job.tenant_id,
        evidence_ids=job.evidence_ids,
    )

    if (
        strategy.strategy_type == "procurement_after_payment"
        and (payment is None or not payment.confirmed)
    ):
        return FulfilmentTriggerResult(
            lifecycle=lifecycle,
            fulfilment_decision=decision,
            triggered=False,
            reason="Confirmed payment is required before fulfilment can proceed.",
        )

    stage_by_decision = {
        "inventory": "inventory_pending",
        "procurement": "procurement_pending",
        "make_to_order": "make_to_order_pending",
        "service_delivery": "service_delivery_pending",
    }

    if decision.decision not in stage_by_decision:
        return FulfilmentTriggerResult(
            lifecycle=lifecycle,
            fulfilment_decision=decision,
            triggered=False,
            reason=(
                "The fulfilment strategy requires a business-specific "
                "workflow before Mananze can select the next lifecycle stage."
            ),
        )

    evidence_ids = tuple(
        dict.fromkeys(
            (
                *lifecycle.evidence_ids,
                *strategy.evidence_ids,
                *(payment.evidence_ids if payment is not None else ()),
            )
        )
    )

    lifecycle = JobLifecycle(
        job_id=lifecycle.job_id,
        tenant_id=lifecycle.tenant_id,
        stage=lifecycle.stage,
        evidence_ids=evidence_ids,
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage=stage_by_decision[decision.decision],
    )

    return FulfilmentTriggerResult(
        lifecycle=lifecycle,
        fulfilment_decision=decision,
        triggered=True,
        reason="Job fulfilment was authorised by the configured business rule.",
    )


__all__ = [
    "FulfilmentTriggerResult",
    "trigger_job_fulfilment",
]
