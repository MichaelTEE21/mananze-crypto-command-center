"""Mananze OS controlled runtime foundation."""

from dataclasses import dataclass

from mananze_os.approval import ApprovalDecision
from mananze_os.approval_gate import ApprovalGate
from mananze_os.compiler import CompiledPlan, IntelligenceCompiler
from mananze_os.domain_qa import DomainQA, QAVerdict
from mananze_os.input_gate import InputGate
from mananze_os.input_request import InputRequest
from mananze_os.workforce_planner import (
    DynamicWorkforcePlan,
    WorkforcePlanner,
)
from mananze_os.work_order import WorkOrder


@dataclass(frozen=True)
class ExecutionEvidence:
    execution_id: str
    action: str
    status: str
    details: str


@dataclass(frozen=True)
class RuntimeReport:
    work_order_id: str
    execution_id: str
    status: str
    evidence: tuple[ExecutionEvidence, ...]


@dataclass(frozen=True)
class RuntimeResult:
    work_order: WorkOrder
    plan: CompiledPlan
    workforce: DynamicWorkforcePlan
    qa: QAVerdict
    approval: ApprovalDecision
    report: RuntimeReport | None = None


class MananzeRuntime:
    """Run the controlled Mananze OS workflow."""

    def __init__(self) -> None:
        self.input_gate = InputGate()
        self.compiler = IntelligenceCompiler()
        self.workforce_planner = WorkforcePlanner()
        self.domain_qa = DomainQA()
        self.approval_gate = ApprovalGate()

    def prepare(self, request: InputRequest) -> RuntimeResult:
        work_order = self.input_gate.accept(request)

        plan = self.compiler.compile(work_order)

        workforce = self.workforce_planner.plan(
            work_order.work_order_id,
            plan.objective,
        )

        qa = self.domain_qa.verify(workforce)

        if not qa.passed:
            raise ValueError("domain QA failed")

        approval = self.approval_gate.request(
            f"exec:{work_order.work_order_id}",
            qa,
        )

        return RuntimeResult(
            work_order=work_order,
            plan=plan,
            workforce=workforce,
            qa=qa,
            approval=approval,
        )

    def execute(
        self,
        prepared: RuntimeResult,
        approved_by: str,
    ) -> RuntimeResult:
        if prepared.approval.status != "pending":
            raise ValueError("execution requires pending approval")

        approved = self.approval_gate.approve(
            prepared.approval,
            approved_by,
        )

        execution_id = approved.execution_id

        evidence = (
            ExecutionEvidence(
                execution_id=execution_id,
                action="controlled_execution",
                status="completed",
                details="Execution simulation completed without external side effects.",
            ),
        )

        report = RuntimeReport(
            work_order_id=prepared.work_order.work_order_id,
            execution_id=execution_id,
            status="completed",
            evidence=evidence,
        )

        return RuntimeResult(
            work_order=prepared.work_order,
            plan=prepared.plan,
            workforce=prepared.workforce,
            qa=prepared.qa,
            approval=approved,
            report=report,
        )


__all__ = [
    "ExecutionEvidence",
    "RuntimeReport",
    "RuntimeResult",
    "MananzeRuntime",
]
