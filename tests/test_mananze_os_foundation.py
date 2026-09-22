import sys

sys.path.insert(0, "src")

from mananze_os import OS_NAME, OS_SHORT_NAME, __version__
from mananze_os.authority import Authority
from mananze_os.execution_context import ExecutionContext
from mananze_os.execution_record import ExecutionRecord
from mananze_os.execution_state import ExecutionState
from mananze_os.identity import PLATFORM_IDENTITY
from mananze_os.work_order import WorkOrder


def test_platform_identity():
    assert OS_NAME == "MANANZE OPERATING SYSTEM"
    assert OS_SHORT_NAME == "MANANZE OS"
    assert __version__ == "0.1.0"
    assert PLATFORM_IDENTITY.short_name == "MANANZE OS"


def test_work_order_contract():
    work_order = WorkOrder(
        work_order_id="WO-1",
        tenant_id="tenant-demo",
        objective="Establish Mananze OS foundation",
    )

    assert work_order.work_order_id == "WO-1"
    assert work_order.tenant_id == "tenant-demo"
    assert work_order.objective == "Establish Mananze OS foundation"
    assert work_order.status == "planned"


def test_authority_contract():
    authority = Authority(
        actor_id="human:tshepo",
        level="human",
        can_execute=True,
        requires_approval=True,
    )

    assert authority.actor_id == "human:tshepo"
    assert authority.level == "human"
    assert authority.can_execute is True
    assert authority.requires_approval is True


def test_execution_context_contract():
    context = ExecutionContext(
        execution_id="exec-001",
        tenant_id="tenant-demo",
        work_order_id="WO-1",
        actor_id="human:tshepo",
    )

    assert context.execution_id == "exec-001"
    assert context.tenant_id == "tenant-demo"
    assert context.work_order_id == "WO-1"
    assert context.actor_id == "human:tshepo"


def test_execution_state_contract():
    state = ExecutionState(execution_id="exec-001")

    assert state.execution_id == "exec-001"
    assert state.status == "created"


def test_execution_state_supports_approval_state():
    state = ExecutionState(
        execution_id="exec-002",
        status="pending_approval",
    )

    assert state.status == "pending_approval"


def test_execution_record_contract():
    work_order = WorkOrder(
        work_order_id="WO-1",
        tenant_id="tenant-demo",
        objective="Establish Mananze OS foundation",
    )

    context = ExecutionContext(
        execution_id="exec-001",
        tenant_id="tenant-demo",
        work_order_id="WO-1",
        actor_id="human:tshepo",
    )

    authority = Authority(
        actor_id="human:tshepo",
        level="human",
        can_execute=True,
        requires_approval=True,
    )

    state = ExecutionState(execution_id="exec-001")

    record = ExecutionRecord(
        work_order=work_order,
        context=context,
        authority=authority,
        state=state,
    )

    assert record.work_order.work_order_id == "WO-1"
    assert record.context.execution_id == "exec-001"
    assert record.authority.actor_id == "human:tshepo"
    assert record.state.status == "created"

from mananze_os.approval import ApprovalDecision


def test_approval_decision_pending():
    decision = ApprovalDecision(
        approval_id="approval-001",
        execution_id="exec-001",
        status="pending",
    )

    assert decision.approval_id == "approval-001"
    assert decision.execution_id == "exec-001"
    assert decision.status == "pending"
    assert decision.decided_by is None
    assert decision.reason is None


def test_approval_decision_approved():
    decision = ApprovalDecision(
        approval_id="approval-002",
        execution_id="exec-002",
        status="approved",
        decided_by="human:tshepo",
        reason="Approved for execution.",
    )

    assert decision.status == "approved"
    assert decision.decided_by == "human:tshepo"
    assert decision.reason == "Approved for execution."

from mananze_os.input_gate import InputGate
from mananze_os.input_request import InputRequest


def test_input_gate_creates_work_order():
    request = InputRequest(
        request_id="req-001",
        tenant_id="tenant-demo",
        actor_id="human:tshepo",
        objective="Increase dental practice patient bookings",
    )

    work_order = InputGate().accept(request)

    assert work_order.work_order_id == "req-001"
    assert work_order.tenant_id == "tenant-demo"
    assert work_order.objective == "Increase dental practice patient bookings"
    assert work_order.status == "planned"


def test_input_gate_rejects_missing_objective():
    request = InputRequest(
        request_id="req-002",
        tenant_id="tenant-demo",
        actor_id="human:tshepo",
        objective="   ",
    )

    try:
        InputGate().accept(request)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "objective is required"

from mananze_os.compiler import IntelligenceCompiler


def test_intelligence_compiler_creates_plan():
    work_order = WorkOrder(
        work_order_id="WO-COMP-001",
        tenant_id="tenant-demo",
        objective="Increase dental practice patient bookings",
    )

    plan = IntelligenceCompiler().compile(work_order)

    assert plan.work_order_id == "WO-COMP-001"
    assert plan.tenant_id == "tenant-demo"
    assert plan.objective == "Increase dental practice patient bookings"
    assert plan.domain == "business"
    assert plan.stages == (
        "understand",
        "plan",
        "execute",
        "verify",
        "report",
    )


def test_intelligence_compiler_compiles_capability_requirements():
    work_order = WorkOrder(
        work_order_id="WO-COMP-003",
        tenant_id="tenant-demo",
        objective="Increase dental practice patient bookings",
    )

    plan = IntelligenceCompiler().compile(work_order)

    assert [requirement.capability_id for requirement in plan.requirements] == [
        "marketing",
        "lead_generation",
        "sales",
        "appointment_booking",
        "customer_communications",
        "retention",
        "revenue",
        "reporting",
    ]


def test_intelligence_compiler_rejects_empty_objective():
    work_order = WorkOrder(
        work_order_id="WO-COMP-002",
        tenant_id="tenant-demo",
        objective="   ",
    )

    try:
        IntelligenceCompiler().compile(work_order)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "objective is required"

from mananze_os.workforce import WorkforceCoordinator
from mananze_os.workforce_planner import WorkforcePlanner


def test_workforce_coordinator_assigns_marketing_sales_revenue():
    workforce = WorkforceCoordinator().assign(
        "WO-WF-001",
        "Increase dental practice patient bookings",
    )

    assert workforce.work_order_id == "WO-WF-001"
    assert [role.role_id for role in workforce.roles] == [
        "marketing",
        "sales",
        "revenue",
    ]


def test_workforce_coordinator_rejects_missing_work_order():
    try:
        WorkforceCoordinator().assign(
            "   ",
            "Increase dental practice patient bookings",
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "work_order_id is required"

from mananze_os.domain_qa import DomainQA


def test_domain_qa_passes_valid_workforce():
    workforce = WorkforcePlanner().plan(
        "WO-QA-001",
        "Increase dental practice patient bookings",
    )

    verdict = DomainQA().verify(workforce)

    assert verdict.work_order_id == "WO-QA-001"
    assert verdict.passed is True
    assert "workforce capabilities selected" in verdict.checks
    assert "work order identity present" in verdict.checks

from mananze_os.approval_gate import ApprovalGate
from mananze_os.domain_qa import QAVerdict


def test_approval_gate_requests_pending_approval():
    verdict = QAVerdict(
        work_order_id="WO-APP-001",
        passed=True,
        checks=("workforce capabilities selected",),
    )

    decision = ApprovalGate().request("exec-001", verdict)

    assert decision.approval_id == "approval:exec-001"
    assert decision.execution_id == "exec-001"
    assert decision.status == "pending"
    assert decision.decided_by is None


def test_approval_gate_approves_pending_request():
    verdict = QAVerdict(
        work_order_id="WO-APP-002",
        passed=True,
        checks=("workforce capabilities selected",),
    )

    gate = ApprovalGate()
    pending = gate.request("exec-002", verdict)
    approved = gate.approve(pending, "human:tshepo")

    assert approved.status == "approved"
    assert approved.decided_by == "human:tshepo"
    assert approved.reason == "Approved for execution."

from mananze_os.authority import Authority
from mananze_os.input_request import InputRequest
from mananze_os.permission import CapabilityPermission
from mananze_os.runtime import MananzeRuntime
from mananze_os.tenant import Tenant


def test_mananze_runtime_end_to_end():
    request = InputRequest(
        request_id="WO-E2E-001",
        tenant_id="dentist-demo",
        actor_id="human:tshepo",
        objective="Increase dental practice patient bookings",
    )

    capabilities = (
        "marketing",
        "lead_generation",
        "sales",
        "appointment_booking",
        "customer_communications",
        "retention",
        "revenue",
        "reporting",
    )

    runtime = MananzeRuntime(
        tenants=(
            Tenant(
                tenant_id="dentist-demo",
                name="Dentist Demo",
            ),
        ),
        authorities=(
            Authority(
                actor_id="human:tshepo",
                level="human",
                can_execute=True,
                requires_approval=True,
            ),
        ),
        permissions=tuple(
            CapabilityPermission(
                actor_id="human:tshepo",
                tenant_id="dentist-demo",
                capability_id=capability_id,
            )
            for capability_id in capabilities
        ),
    )

    prepared = runtime.prepare(request)

    assert prepared.work_order.work_order_id == "WO-E2E-001"
    assert prepared.plan.domain == "business"
    assert [role.role_id for role in prepared.workforce.roles] == [
        "marketing",
        "lead_generation",
        "sales",
        "appointment_booking",
        "customer_communications",
        "retention",
        "revenue",
        "reporting",
    ]
    assert prepared.qa.passed is True
    assert prepared.approval.status == "pending"

    completed = runtime.execute(
        prepared,
        "human:tshepo",
    )

    assert completed.approval.status == "approved"
    assert completed.report is not None
    assert completed.report.status == "completed"
    assert len(completed.report.evidence) == 4
    assert completed.report.evidence[0].action == "policy_decision"
    assert completed.report.evidence[0].status == "approval_required"
    assert completed.report.evidence[1].action == "authorization_decision"
    assert completed.report.evidence[1].status == "allowed"
    assert completed.report.evidence[2].action == "workforce_assignment"
    assert completed.report.evidence[2].status == "validated"
    assert "assignment_count=8" in completed.report.evidence[2].details
    assert completed.report.evidence[3].action == "controlled_execution"
    assert completed.report.evidence[3].status == "completed"








def test_mananze_runtime_registers_planned_roles_in_workforce_fabric():
    request = InputRequest(
        request_id="WO-FABRIC-001",
        tenant_id="dentist-demo",
        actor_id="human:tshepo",
        objective="Increase dental practice patient bookings",
    )

    capabilities = (
        "marketing",
        "lead_generation",
        "sales",
        "appointment_booking",
        "customer_communications",
        "retention",
        "revenue",
        "reporting",
    )

    runtime = MananzeRuntime(
        tenants=(
            Tenant(
                tenant_id="dentist-demo",
                name="Dentist Demo",
            ),
        ),
        authorities=(
            Authority(
                actor_id="human:tshepo",
                level="human",
                can_execute=True,
                requires_approval=True,
            ),
        ),
        permissions=tuple(
            CapabilityPermission(
                actor_id="human:tshepo",
                tenant_id="dentist-demo",
                capability_id=capability_id,
            )
            for capability_id in capabilities
        ),
    )

    prepared = runtime.prepare(request)

    assert [
        role.role_id
        for role in runtime.workforce_fabric.list_roles()
    ] == list(capabilities)

    assert [
        runtime.workforce_fabric.get_role(role.role_id).capability_ids
        for role in prepared.workforce.roles
    ] == [(capability_id,) for capability_id in capabilities]

    assert [
        runtime.workforce_fabric.get_role(role.role_id).skill_ids
        for role in prepared.workforce.roles
    ] == [
        role.skill_ids
        for role in prepared.workforce.roles
    ]


def test_mananze_runtime_creates_execution_scoped_workforce_assignments():
    request = InputRequest(
        request_id="WO-ASSIGN-001",
        tenant_id="dentist-demo",
        actor_id="human:tshepo",
        objective="Increase dental practice patient bookings",
    )

    capabilities = (
        "marketing",
        "lead_generation",
        "sales",
        "appointment_booking",
        "customer_communications",
        "retention",
        "revenue",
        "reporting",
    )

    runtime = MananzeRuntime(
        tenants=(
            Tenant(
                tenant_id="dentist-demo",
                name="Dentist Demo",
            ),
        ),
        authorities=(
            Authority(
                actor_id="human:tshepo",
                level="human",
                can_execute=True,
                requires_approval=True,
            ),
        ),
        permissions=tuple(
            CapabilityPermission(
                actor_id="human:tshepo",
                tenant_id="dentist-demo",
                capability_id=capability_id,
            )
            for capability_id in capabilities
        ),
    )

    prepared = runtime.prepare(request)

    assignments_before_approval = (
        runtime.workforce_fabric.list_assignments_for_execution(
            "exec:WO-ASSIGN-001"
        )
    )

    assert assignments_before_approval == ()

    completed = runtime.execute(
        prepared,
        "human:tshepo",
    )

    assignments = runtime.workforce_fabric.list_assignments_for_execution(
        "exec:WO-ASSIGN-001"
    )

    assert len(assignments) == len(capabilities)
    assert [
        assignment.assignment_id
        for assignment in assignments
    ] == [
        f"assignment:WO-ASSIGN-001:{capability_id}"
        for capability_id in capabilities
    ]
    assert [
        assignment.node_id
        for assignment in assignments
    ] == [
        f"node:{capability_id}"
        for capability_id in capabilities
    ]
    assert [
        assignment.role_id
        for assignment in assignments
    ] == list(capabilities)
    assert all(
        assignment.execution_id == "exec:WO-ASSIGN-001"
        for assignment in assignments
    )

    assert completed.approval.status == "approved"
    assert prepared.work_order.work_order_id == "WO-ASSIGN-001"

