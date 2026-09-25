"""Governed execution controller for the Mananze OS control plane."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mananze_os.action_gate import ActionGate, ActionRequest
from mananze_os.approval import ApprovalDecision
from mananze_os.approval_gate import ApprovalGate
from mananze_os.authorization import (
    AuthorizationDecision,
    AuthorizationEngine,
)
from mananze_os.capability_workforce_bridge import CapabilityWorkforcePlan
from mananze_os.domain_qa import DomainQA, QAVerdict
from mananze_os.execution_context_integrity import (
    ExecutionContext,
    ExecutionContextIntegrity,
)
from mananze_os.policy import Policy
from mananze_os.policy_engine import PolicyDecision, PolicyEngine


ExecutionDisposition = Literal[
    "allowed",
    "approval_required",
    "denied",
]


@dataclass(frozen=True)
class GovernedExecutionResult:
    """Final governance decision before external provider execution."""

    execution_id: str
    tenant_id: str
    work_order_id: str
    task_id: str
    actor_id: str
    capability_id: str
    action: str
    disposition: ExecutionDisposition
    reasons: tuple[str, ...] = ()
    context: ExecutionContext | None = None
    qa: QAVerdict | None = None
    policy: PolicyDecision | None = None
    authorization: AuthorizationDecision | None = None
    approval: ApprovalDecision | None = None
    action_request: ActionRequest | None = None

    @property
    def allowed(self) -> bool:
        return self.disposition == "allowed"

    @property
    def requires_approval(self) -> bool:
        return self.disposition == "approval_required"


class GovernedExecutionController:
    """
    Orchestrate the Mananze execution control plane.

    This controller does not execute external actions.

    It validates execution lineage, evaluates policy, checks authorization,
    performs domain QA, evaluates the Action Gate, and requests approval
    when required. External provider execution remains downstream of this
    boundary.
    """

    def __init__(
        self,
        *,
        policy_engine: PolicyEngine | None = None,
        authorization_engine: AuthorizationEngine | None = None,
        domain_qa: DomainQA | None = None,
        action_gate: ActionGate | None = None,
        approval_gate: ApprovalGate | None = None,
    ) -> None:
        self.policy_engine = policy_engine or PolicyEngine()
        self.authorization_engine = (
            authorization_engine or AuthorizationEngine()
        )
        self.domain_qa = domain_qa or DomainQA()
        self.action_gate = action_gate or ActionGate()
        self.approval_gate = approval_gate or ApprovalGate()

    def evaluate(
        self,
        *,
        plan: CapabilityWorkforcePlan,
        execution_id: str,
        task_id: str,
        actor_id: str,
        capability_id: str,
        action: str,
        authority,
        tenant,
        permissions,
        policy: tuple[Policy, ...] = (),
        tool_id: str = "mananze",
        payload: dict | None = None,
        risk: str = "medium",
        requires_approval: bool = False,
        economic_allowed: bool = True,
    ) -> GovernedExecutionResult:
        if not execution_id.strip():
            raise ValueError("execution_id is required")

        if not task_id.strip():
            raise ValueError("task_id is required")

        if not actor_id.strip():
            raise ValueError("actor_id is required")

        if not capability_id.strip():
            raise ValueError("capability_id is required")

        if not action.strip():
            raise ValueError("action is required")

        matching_nodes = tuple(
            node
            for node in plan.execution_graph.nodes
            if node.capability_id == capability_id
        )

        if len(matching_nodes) != 1:
            raise ValueError(
                "capability_id must identify exactly one execution node"
            )

        node = matching_nodes[0]

        if node.tool_id is not None and node.tool_id != tool_id:
            raise ValueError(
                "tool_id does not match the execution node"
            )

        work_order = _build_work_order(plan)

        compiled = _compile_plan(
            work_order=work_order,
            capability_ids=tuple(
                selection.capability_id
                for selection in plan.selections
            ),
        )

        workforce = plan.dynamic_plan

        context = ExecutionContextIntegrity().bind(
            work_order=work_order,
            plan=compiled,
            workforce=workforce,
            execution_id=execution_id,
            task_id=task_id,
        )

        if context.tenant_id != plan.tenant_id:
            raise ValueError("execution tenant does not match plan tenant")

        qa = self.domain_qa.verify(workforce)

        if not qa.passed:
            return GovernedExecutionResult(
                execution_id=execution_id,
                tenant_id=plan.tenant_id,
                work_order_id=plan.work_order_id,
                task_id=task_id,
                actor_id=actor_id,
                capability_id=capability_id,
                action=action,
                disposition="denied",
                reasons=qa.checks,
                context=context,
                qa=qa,
            )

        policy_decision = self.policy_engine.evaluate(
            workforce,
            policies=policy,
        )

        if policy_decision.effect == "deny":
            return GovernedExecutionResult(
                execution_id=execution_id,
                tenant_id=plan.tenant_id,
                work_order_id=plan.work_order_id,
                task_id=task_id,
                actor_id=actor_id,
                capability_id=capability_id,
                action=action,
                disposition="denied",
                reasons=policy_decision.reasons,
                context=context,
                qa=qa,
                policy=policy_decision,
            )

        authorization = self.authorization_engine.evaluate(
            execution_id=execution_id,
            authority=authority,
            tenant=tenant,
            workforce=workforce,
            permissions=permissions,
        )

        if not authorization.allowed:
            return GovernedExecutionResult(
                execution_id=execution_id,
                tenant_id=plan.tenant_id,
                work_order_id=plan.work_order_id,
                task_id=task_id,
                actor_id=actor_id,
                capability_id=capability_id,
                action=action,
                disposition="denied",
                reasons=authorization.reasons,
                context=context,
                qa=qa,
                policy=policy_decision,
                authorization=authorization,
            )

        action_request = ActionRequest(
            action_id=f"{execution_id}:{capability_id}",
            tenant_id=plan.tenant_id,
            execution_id=execution_id,
            task_id=task_id,
            actor_id=actor_id,
            tool_id=tool_id,
            capability_id=capability_id,
            action=action.strip(),
            risk=risk,
            payload=payload or {},
            requires_approval=requires_approval,
        )

        action_decision = self.action_gate.evaluate(
            action_request,
            tenant_allowed=True,
            permission_allowed=True,
            policy_effect=policy_decision.effect,
            economic_allowed=economic_allowed,
        )

        if not action_decision.allowed:
            if action_decision.effect != "approval_required":
                return GovernedExecutionResult(
                    execution_id=execution_id,
                    tenant_id=plan.tenant_id,
                    work_order_id=plan.work_order_id,
                    task_id=task_id,
                    actor_id=actor_id,
                    capability_id=capability_id,
                    action=action,
                    disposition="denied",
                    reasons=action_decision.reasons,
                    context=context,
                    qa=qa,
                    policy=policy_decision,
                    authorization=authorization,
                    action_request=action_request,
                )

            approval = self.approval_gate.request(
                execution_id=execution_id,
                qa_verdict=qa,
            )

            return GovernedExecutionResult(
                execution_id=execution_id,
                tenant_id=plan.tenant_id,
                work_order_id=plan.work_order_id,
                task_id=task_id,
                actor_id=actor_id,
                capability_id=capability_id,
                action=action,
                disposition="approval_required",
                reasons=action_decision.reasons,
                context=context,
                qa=qa,
                policy=policy_decision,
                authorization=authorization,
                approval=approval,
                action_request=action_request,
            )

        return GovernedExecutionResult(
            execution_id=execution_id,
            tenant_id=plan.tenant_id,
            work_order_id=plan.work_order_id,
            task_id=task_id,
            actor_id=actor_id,
            capability_id=capability_id,
            action=action,
            disposition="allowed",
            reasons=action_decision.reasons,
            context=context,
            qa=qa,
            policy=policy_decision,
            authorization=authorization,
            action_request=action_request,
        )


def _build_work_order(plan: CapabilityWorkforcePlan):
    from mananze_os.work_order import WorkOrder

    return WorkOrder(
        work_order_id=plan.work_order_id,
        tenant_id=plan.tenant_id,
        objective=plan.objective,
    )


def _compile_plan(*, work_order, capability_ids):
    from mananze_os.compiler import IntelligenceCompiler

    return IntelligenceCompiler().compile(
        work_order,
        candidate_capability_ids=capability_ids,
    )


__all__ = [
    "ExecutionDisposition",
    "GovernedExecutionResult",
    "GovernedExecutionController",
]
