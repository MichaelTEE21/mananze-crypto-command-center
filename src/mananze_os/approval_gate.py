"""Mananze OS human approval gate."""

from mananze_os.approval import ApprovalDecision
from mananze_os.domain_qa import QAVerdict


class ApprovalGate:
    """Control whether a verified plan may proceed to execution."""

    def request(
        self,
        execution_id: str,
        qa_verdict: QAVerdict,
    ) -> ApprovalDecision:
        if not execution_id.strip():
            raise ValueError("execution_id is required")

        if not qa_verdict.passed:
            raise ValueError("cannot request approval for failed QA")

        return ApprovalDecision(
            approval_id=f"approval:{execution_id}",
            execution_id=execution_id,
            status="pending",
        )

    def approve(
        self,
        decision: ApprovalDecision,
        approved_by: str,
        reason: str = "Approved for execution.",
    ) -> ApprovalDecision:
        if decision.status != "pending":
            raise ValueError("approval is not pending")

        if not approved_by.strip():
            raise ValueError("approved_by is required")

        return ApprovalDecision(
            approval_id=decision.approval_id,
            execution_id=decision.execution_id,
            status="approved",
            decided_by=approved_by,
            reason=reason,
        )


__all__ = ["ApprovalGate"]
