"""Mananze OS controlled runtime foundation."""

from dataclasses import dataclass

from mananze_os.approval import ApprovalDecision
from mananze_os.approval_gate import ApprovalGate
from mananze_os.compiler import CompiledPlan, IntelligenceCompiler
from mananze_os.domain_qa import DomainQA, QAVerdict
from mananze_os.input_gate import InputGate
from mananze_os.input_request import InputRequest
from mananze_os.policy_decision import PolicyDecision
from mananze_os.policy_engine import PolicyEngine
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
    policy: PolicyDecision
    qa: QAVerdict
    approval: ApprovalDecision
    report: RuntimeReport | None = None


class MananzeRuntime:
    """Run the controlled Mananze OS workflow."""

    def __init__(self) -> None:
        self.input_gate = InputGate()
        self.compiler = IntelligenceCompiler()
        self.workforce_planner = WorkforcePlanner()
        self.policy_engine = PolicyEngine()
        self.domain_qa = DomainQA()
        self.approval_gate = ApprovalGate()

    def prepare(self, request: InputRequest) -> RuntimeResult:
        work_order = self.input_gate.accept(request)

        plan = self.compiler.compile(work_order)

        workforce = self.workforce_planner.plan(
            work_order.work_order_id,
            plan.objective,
        )

        policy = self.policy_engine.evaluate(workforce)

        if policy.effect == "deny":
            raise PermissionError(
                "policy denied execution: "
                + "; ".join(policy.reasons)
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
            policy=policy,
            qa=qa,
            approval=approval,
        )

    def execute(
        self,
        prepared: RuntimeResult,
        approved_by: str,
    ) -> RuntimeResult:
        if prepared.policy.effect == "deny":
            raise PermissionError(
                "policy denied execution: "
                + "; ".join(prepared.policy.reasons)
            )

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
                action="policy_decision",
                status=prepared.policy.effect,
                details=(
                    f"risk={prepared.policy.risk}; "
                    f"autonomy_level={prepared.policy.autonomy_level}; "
                    f"reasons={' | '.join(prepared.policy.reasons)}"
                ),
            ),
            ExecutionEvidence(
                execution_id=execution_id,
                action="controlled_execution",
                status="completed",
                details=(
                    "Execution simulation completed without "
                    "external side effects."
                ),
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
            policy=prepared.policy,
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
