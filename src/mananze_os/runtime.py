"""Mananze OS controlled runtime foundation."""

from dataclasses import dataclass
from uuid import uuid4

from mananze_os.action_gate import ActionGate, ActionGateDecision, ActionRequest
from mananze_os.approval import ApprovalDecision
from mananze_os.approval_gate import ApprovalGate
from mananze_os.authority import Authority
from mananze_os.authorization import (
    AuthorizationDecision,
    AuthorizationEngine,
)
from mananze_os.compiler import CompiledPlan, IntelligenceCompiler
from mananze_os.domain_qa import DomainQA, QAVerdict
from mananze_os.execution_evidence import ExecutionEvidence
from mananze_os.execution_graph import ExecutionNode
from mananze_os.execution_context_integrity import ExecutionContextIntegrity
from mananze_os.execution_lifecycle import ExecutionLifecycle
from mananze_os.execution_state import ExecutionState
from mananze_os.execution_verifier import (
    ExecutionVerification,
    ExecutionVerifier,
)
from mananze_os.input_gate import InputGate
from mananze_os.input_request import InputRequest
from mananze_os.request_lifecycle import RequestLifecycle, RequestState
from mananze_os.processing_mode_decision import ProcessingModeDecider
from mananze_os.permission import CapabilityPermission
from mananze_os.policy_decision import PolicyDecision
from mananze_os.provider_router import ProviderRouter, ProviderRoutingResult
from mananze_os.policy_engine import PolicyEngine
from mananze_os.quality_controller import QualityAssessment, QualityControllerIntelligence
from mananze_os.task_scheduler import ScheduledTask, TaskScheduler
from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.tenant import Tenant
from mananze_os.workforce_planner import (
    DynamicWorkforcePlan,
    WorkforcePlanner,
)
from mananze_os.work_order import WorkOrder
from mananze_os.workforce_fabric import WorkforceFabric
from mananze_os.workforce_role import WorkforceRole


@dataclass(frozen=True)
class ExecutionRequest:
    """Request passed from governed runtime execution into provider routing."""

    tenant_id: str
    execution_id: str
    tool_id: str
    operation: str
    payload: dict
    authorization_id: str
    approval_id: str | None = None

    def __post_init__(self) -> None:
        fields = {
            "tenant_id": self.tenant_id,
            "execution_id": self.execution_id,
            "tool_id": self.tool_id,
            "operation": self.operation,
            "authorization_id": self.authorization_id,
        }

        for name, value in fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")

        if self.approval_id is not None:
            if not isinstance(self.approval_id, str) or not self.approval_id.strip():
                raise ValueError("approval_id cannot be blank")

        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a dict")


class RuntimeExecutionBoundary:
    """Controlled bridge from MananzeRuntime into ProviderRouter."""

    def __init__(self, router: ProviderRouter) -> None:
        if not isinstance(router, ProviderRouter):
            raise TypeError("router must be a ProviderRouter")
        self.router = router

    def execute(self, request: ExecutionRequest) -> ProviderRoutingResult:
        if not isinstance(request, ExecutionRequest):
            raise TypeError("request must be an ExecutionRequest")

        return self.router.route(
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            operation=request.operation,
            payload=request.payload,
        )


@dataclass(frozen=True)
class RuntimeReport:
    work_order_id: str
    execution_id: str
    status: str
    evidence: tuple[ExecutionEvidence, ...]
    verification: ExecutionVerification


@dataclass(frozen=True)
class RuntimeResult:
    work_order: WorkOrder
    plan: CompiledPlan
    workforce: DynamicWorkforcePlan
    policy: PolicyDecision
    authorization: AuthorizationDecision
    qa: QAVerdict
    quality: QualityAssessment
    action_gate: ActionGateDecision
    approval: ApprovalDecision
    execution_state: ExecutionState
    request_state: RequestState
    report: RuntimeReport | None = None


class MananzeRuntime:
    """Run the controlled Mananze OS workflow."""

    def __init__(
        self,
        tenants: tuple[Tenant, ...] = (),
        authorities: tuple[Authority, ...] = (),
        permissions: tuple[CapabilityPermission, ...] = (),
        task_store: SQLiteTaskStore | None = None,
        provider_router: ProviderRouter | None = None,
    ) -> None:
        self.input_gate = InputGate()
        self.action_gate = ActionGate()
        self.compiler = IntelligenceCompiler()
        self.workforce_planner = WorkforcePlanner()
        self.workforce_fabric = WorkforceFabric()
        self.policy_engine = PolicyEngine()
        self.authorization_engine = AuthorizationEngine()
        self.domain_qa = DomainQA()
        self.quality_controller = QualityControllerIntelligence()
        self.approval_gate = ApprovalGate()
        self.execution_lifecycle = ExecutionLifecycle()
        self.request_lifecycle = RequestLifecycle()
        self.processing_mode_decider = ProcessingModeDecider()
        self.execution_context_integrity = ExecutionContextIntegrity()
        self.task_store = task_store
        self.execution_verifier = ExecutionVerifier()
        self.task_scheduler = TaskScheduler()
        self.provider_router = provider_router
        self.runtime_execution_boundary = (
            RuntimeExecutionBoundary(provider_router)
            if provider_router is not None
            else None
        )
        self.tenants = tenants
        self.authorities = authorities
        self.permissions = permissions

    def _get_tenant(self, tenant_id: str) -> Tenant:
        for tenant in self.tenants:
            if tenant.tenant_id == tenant_id:
                return tenant

        raise PermissionError(
            f"unknown tenant: {tenant_id}"
        )

    def _get_authority(self, actor_id: str) -> Authority:
        for authority in self.authorities:
            if authority.actor_id == actor_id:
                return authority

        raise PermissionError(
            f"unknown actor authority: {actor_id}"
        )

    def prepare(self, request: InputRequest) -> RuntimeResult:
        request_state = RequestState(request_id=request.request_id)

        request_state, _ = self.request_lifecycle.transition(
            request_state,
            "validating",
        )

        work_order = self.input_gate.accept(request)

        request_state, _ = self.request_lifecycle.transition(
            request_state,
            "classifying",
        )

        request_state, _ = self.request_lifecycle.transition(
            request_state,
            "compiling",
        )

        plan = self.compiler.compile(work_order)

        request_state, _ = self.request_lifecycle.transition(
            request_state,
            "planning",
        )

        workforce = self.workforce_planner.plan_from_requirements(
            work_order.work_order_id,
            plan.objective,
            plan.requirements,
        )

        for planned_role in workforce.roles:
            self.workforce_fabric.register_role(
                WorkforceRole(
                    role_id=planned_role.role_id,
                    name=planned_role.name,
                    description=planned_role.objective,
                    capability_ids=(planned_role.capability_id,),
                    skill_ids=planned_role.skill_ids,
                )
            )

        policy = self.policy_engine.evaluate(workforce)

        if policy.effect == "deny":
            raise PermissionError(
                "policy denied execution: "
                + "; ".join(policy.reasons)
            )

        tenant = self._get_tenant(work_order.tenant_id)
        authority = self._get_authority(request.actor_id)
        execution_id = f"exec:{work_order.work_order_id}"

        authorization = self.authorization_engine.evaluate(
            execution_id=execution_id,
            authority=authority,
            tenant=tenant,
            workforce=workforce,
            permissions=self.permissions,
        )

        if not authorization.allowed:
            raise PermissionError(
                "authorization denied: "
                + "; ".join(authorization.reasons)
            )

        qa = self.domain_qa.verify(workforce)

        if not qa.passed:
            raise ValueError("domain QA failed")

        quality = self.quality_controller.assess_workforce_plan(
            assessment_id=f"qci:{work_order.work_order_id}",
            tenant_id=work_order.tenant_id,
            workforce=workforce,
        )

        if quality.failed:
            raise ValueError(
                "quality controller assessment failed: "
                + "; ".join(
                    finding.message
                    for finding in quality.findings
                    if finding.disposition == "fail"
                )
            )
        action_request = ActionRequest(
            action_id=f"action:{work_order.work_order_id}",
            tenant_id=work_order.tenant_id,
            execution_id=execution_id,
            task_id=f"task:{work_order.work_order_id}",
            actor_id=request.actor_id,
            tool_id="mananze:controlled_execution",
            capability_id="mananze:runtime_controlled_execution",
            action="controlled_execution",
            risk=policy.risk,
            payload={
                "work_order_id": work_order.work_order_id,
                "execution_id": execution_id,
                "workforce_role_ids": tuple(
                    role.role_id for role in workforce.roles
                ),
            },
            requires_approval=authority.requires_approval,
        )

        action_gate = self.action_gate.evaluate(
            action_request,
            tenant_allowed=tenant.active,
            permission_allowed=authorization.allowed,
            policy_effect=policy.effect,
        )

        if action_gate.effect == "deny":
            raise PermissionError(
                "action gate denied execution: "
                + "; ".join(action_gate.reasons)
            )
        task_id = f"task:{work_order.work_order_id}"

        processing_mode = self.processing_mode_decider.decide(
            request.processing_mode
        )

        scheduled_task = ScheduledTask(
            task_id=task_id,
            tenant_id=work_order.tenant_id,
            execution_id=execution_id,
            priority=0,
            execution_class=processing_mode.processing_mode,
        )

        self.task_scheduler.submit(scheduled_task)
        if self.task_store is not None:
            self.task_store.save(scheduled_task)

        request_state, _ = self.request_lifecycle.transition(
            request_state,
            "scheduled",
        )

        execution_state = ExecutionState(
            execution_id=execution_id,
            status="created",
        )

        execution_state, _ = self.execution_lifecycle.transition(
            execution_state,
            "pending_approval",
        )

        approval = self.approval_gate.request(
            execution_id,
            qa,
        )

        request_state, _ = self.request_lifecycle.transition(
            request_state,
            "waiting_approval",
        )

        return RuntimeResult(
            work_order=work_order,
            plan=plan,
            workforce=workforce,
            policy=policy,
            authorization=authorization,
            qa=qa,
            quality=quality,
            action_gate=action_gate,
            approval=approval,
            execution_state=execution_state,
            request_state=request_state,
        )

    def recover_stale_tasks(
        self,
        stale_after,
        tenant_id: str | None = None,
        limit: int = 100,
        now=None,
    ) -> tuple[ScheduledTask, ...]:
        """
        Recover stale durable execution leases.

        SQLiteTaskStore remains the authoritative owner of task state,
        lease ownership, retry accounting, and atomic recovery. Runtime
        only coordinates discovery and recovery; it does not introduce
        a competing control plane.
        """
        if self.task_store is None:
            raise RuntimeError(
                "durable task recovery requires a configured task store"
            )

        stale_tasks = self.task_store.stale_running_tasks(
            stale_after=stale_after,
            tenant_id=tenant_id,
            limit=limit,
            now=now,
        )

        recovered: list[ScheduledTask] = []

        for task in stale_tasks:
            recovered_task = self.task_store.recover(
                task_id=task.task_id,
                stale_after=stale_after,
                now=now,
            )

            if recovered_task.status == "queued":
                self.task_scheduler.restore_queued(recovered_task)

            recovered.append(recovered_task)

        return tuple(recovered)

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

        if not prepared.authorization.allowed:
            raise PermissionError(
                "authorization denied: "
                + "; ".join(prepared.authorization.reasons)
            )

        if prepared.approval.status != "pending":
            raise ValueError("execution requires pending approval")

        if (
            prepared.execution_state.execution_id
            != prepared.approval.execution_id
        ):
            raise ValueError(
                "execution state and approval execution IDs do not match"
            )

        approver = next(
            (
                authority
                for authority in self.authorities
                if authority.actor_id == approved_by
            ),
            None,
        )

        if approver is None or approver.level != "human" or not approver.can_execute:
            raise PermissionError(
                "approved_by is not an authorized human execution authority"
            )

        approved = self.approval_gate.approve(
            prepared.approval,
            approved_by,
        )

        execution_state, _ = self.execution_lifecycle.transition(
            prepared.execution_state,
            "approved",
        )

        request_state, _ = self.request_lifecycle.transition(
            prepared.request_state,
            "executing",
        )

        execution_id = approved.execution_id

        task_id = f"task:{prepared.work_order.work_order_id}"
        lease_id = (
            f"lease:{execution_id}:"
            f"worker:{uuid4().hex}"
        )

        if self.task_store is not None:
            started_task = self.task_store.start(
                task_id=task_id,
                lease_id=lease_id,
            )

            # Establish the first worker heartbeat immediately after
            # acquiring the durable execution lease. Subsequent
            # heartbeats are owned by the worker executing the task.
            self.task_store.heartbeat(
                task_id=task_id,
                lease_id=lease_id,
            )

            # Claim the protected logical operation before creating any
            # downstream execution effects. The operation identity is
            # stable for this work order/execution and therefore remains
            # unchanged across retry of the same durable task.
            operation_key = self.task_store.operation_key(
                prepared.work_order.tenant_id,
                task_id,
                execution_id,
                "controlled-execution",
            )

            claimed_operation = self.task_store.claim_operation(
                tenant_id=prepared.work_order.tenant_id,
                operation_key=operation_key,
                task_id=task_id,
                execution_id=execution_id,
                lease_id=lease_id,
            )

            if not claimed_operation:
                existing_operation = self.task_store.idempotency_record(
                    tenant_id=prepared.work_order.tenant_id,
                    operation_key=operation_key,
                )

                if existing_operation is None:
                    raise RuntimeError(
                        "idempotency claim was lost without a durable record"
                    )

                if existing_operation["status"] == "completed":
                    raise RuntimeError(
                        "protected operation already completed; "
                        "replay must be handled by the execution caller"
                    )

                raise RuntimeError(
                    "protected operation is already in progress"
                )

        else:
            operation_key = None

        for planned_role in prepared.workforce.roles:
            self.workforce_fabric.assign_role(
                assignment_id=(
                    f"assignment:"
                    f"{prepared.work_order.work_order_id}:"
                    f"{planned_role.role_id}"
                ),
                execution_id=execution_id,
                node=ExecutionNode(
                    node_id=f"node:{planned_role.role_id}",
                    capability_id=planned_role.capability_id,
                    skill_ids=planned_role.skill_ids,
                ),
                role_id=planned_role.role_id,
            )

        execution_state, _ = self.execution_lifecycle.transition(
            execution_state,
            "running",
        )

        assignments = (
            self.workforce_fabric.list_assignments_for_execution(
                execution_id
            )
        )

        if not assignments:
            raise ValueError(
                "execution requires workforce assignments"
            )

        expected_role_ids = {
            role.role_id
            for role in prepared.workforce.roles
        }

        assigned_role_ids = {
            assignment.role_id
            for assignment in assignments
        }

        if assigned_role_ids != expected_role_ids:
            raise ValueError(
                "workforce assignments do not match planned roles"
            )

        execution_state, _ = self.execution_lifecycle.transition(
            execution_state,
            "qa",
        )

        execution_state, _ = self.execution_lifecycle.transition(
            execution_state,
            "executing",
        )

        provider_result = None

        if self.runtime_execution_boundary is not None:
            provider_result = self.runtime_execution_boundary.execute(
                ExecutionRequest(
                    tenant_id=prepared.work_order.tenant_id,
                    execution_id=execution_id,
                    tool_id="mananze:controlled_execution",
                    operation="controlled_execution",
                    payload={
                        "work_order_id": prepared.work_order.work_order_id,
                        "execution_id": execution_id,
                        "workforce_role_ids": tuple(
                            role.role_id
                            for role in prepared.workforce.roles
                        ),
                    },
                    authorization_id=f"authorization:{execution_id}",
                    approval_id=approved.approval_id,
                )
            )

            if not provider_result.success:
                raise RuntimeError(
                    "provider execution failed: "
                    + (
                        provider_result.error
                        or "unknown provider execution failure"
                    )
                )

        controlled_execution_details = (
            "Execution simulation completed without external side effects."
            if provider_result is None
            else (
                "Provider execution completed through the centralized "
                "ProviderRouter and ProviderExecutionGateway; "
                f"provider_id={provider_result.provider_id}; "
                f"cost={provider_result.cost} "
                f"{provider_result.cost_currency}."
            )
        )

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
                action="authorization_decision",
                status="allowed",
                details=(
                    f"actor_id={prepared.authorization.actor_id}; "
                    f"tenant_id={prepared.authorization.tenant_id}; "
                    f"allowed={prepared.authorization.allowed}; "
                    f"reasons={' | '.join(prepared.authorization.reasons)}"
                ),
            ),
            ExecutionEvidence(
                execution_id=execution_id,
                action="workforce_assignment",
                status="validated",
                details=(
                    f"assignment_count={len(assignments)}; "
                    f"assignment_ids={','.join(assignment.assignment_id for assignment in assignments)}"
                ),
            ),
            ExecutionEvidence(
                execution_id=execution_id,
                action="controlled_execution",
                status="completed",
                details=controlled_execution_details,
            ),
        )

        request_state, _ = self.request_lifecycle.transition(
            request_state,
            "verifying",
        )

        execution_state, _ = self.execution_lifecycle.transition(
            execution_state,
            "completed",
        )

        verification = self.execution_verifier.verify(
            execution_state,
            evidence,
        )

        if not verification.verified:
            raise RuntimeError(
                "execution verification failed: "
                + "; ".join(verification.reasons)
            )

        if self.task_store is not None and operation_key is not None:
            self.task_store.complete_operation(
                tenant_id=prepared.work_order.tenant_id,
                operation_key=operation_key,
                lease_id=lease_id,
                result={
                    "work_order_id": prepared.work_order.work_order_id,
                    "execution_id": execution_id,
                    "status": execution_state.status,
                },
                evidence={
                    "verification": verification.verified,
                    "evidence_count": len(evidence),
                },
            )

        if self.task_store is not None:
            self.task_store.complete(
                task_id=task_id,
                lease_id=lease_id,
            )

        request_state, _ = self.request_lifecycle.transition(
            request_state,
            "completed",
        )

        report = RuntimeReport(
            work_order_id=prepared.work_order.work_order_id,
            execution_id=execution_id,
            status=execution_state.status,
            evidence=evidence,
            verification=verification,
        )

        return RuntimeResult(
            work_order=prepared.work_order,
            plan=prepared.plan,
            workforce=prepared.workforce,
            policy=prepared.policy,
            authorization=prepared.authorization,
            qa=prepared.qa,
            quality=prepared.quality,
            action_gate=prepared.action_gate,
            approval=approved,
            execution_state=execution_state,
            request_state=request_state,
            report=report,
        )

    def claim_next_task(
        self,
        *,
        tenant_id: str,
        lease_id: str,
        now=None,
    ) -> ScheduledTask | None:
        """Claim the next durable task for a worker.

        The scheduler selects eligible work, while the durable task store
        remains authoritative for task state and execution leases.
        """
        task = self.task_scheduler.next_task(
            tenant_id=tenant_id,
            now=now,
        )

        if task is None:
            return None

        if self.task_store is None:
            raise RuntimeError(
                "durable task store is required for worker continuation"
            )

        effective_lease_id = lease_id

        started_task = self.task_store.start(
            task_id=task.task_id,
            lease_id=effective_lease_id,
            now=now,
        )

        self.task_scheduler.mark_running(task.task_id)

        return started_task

    def heartbeat_task(
        self,
        *,
        task_id: str,
        lease_id: str,
        now=None,
    ) -> ScheduledTask:
        """Renew a worker's durable execution lease."""
        if self.task_store is None:
            raise RuntimeError(
                "durable task store is required for worker continuation"
            )

        return self.task_store.heartbeat(
            task_id=task_id,
            lease_id=lease_id,
            now=now,
        )

    def complete_task(
        self,
        *,
        task_id: str,
        lease_id: str,
        now=None,
    ) -> ScheduledTask:
        """Complete a task only when the supplied lease is authoritative."""
        if self.task_store is None:
            raise RuntimeError(
                "durable task store is required for worker continuation"
            )

        completed_task = self.task_store.complete(
            task_id=task_id,
            lease_id=lease_id,
            now=now,
        )

        self.task_scheduler.mark_completed(task_id)

        return completed_task

__all__ = [
    "ExecutionEvidence",
    "ExecutionRequest",
    "RuntimeExecutionBoundary",
    "RuntimeReport",
    "RuntimeResult",
    "MananzeRuntime",
]
