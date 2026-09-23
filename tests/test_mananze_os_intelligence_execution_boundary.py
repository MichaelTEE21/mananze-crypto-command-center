from dataclasses import replace

import pytest

from mananze_os.approval import ApprovalDecision
from mananze_os.authority import Authority
from mananze_os.input_request import InputRequest
from mananze_os.intelligence_fabric import IntelligenceObservation
from mananze_os.permission import CapabilityPermission
from mananze_os.runtime import MananzeRuntime
from mananze_os.tenant import Tenant


CAPABILITIES = (
    "marketing",
    "lead_generation",
    "sales",
    "appointment_booking",
    "customer_communications",
    "retention",
    "revenue",
    "reporting",
)


def build_runtime() -> MananzeRuntime:
    return MananzeRuntime(
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
            for capability_id in CAPABILITIES
        ),
    )


def build_request(request_id: str) -> InputRequest:
    return InputRequest(
        request_id=request_id,
        tenant_id="dentist-demo",
        actor_id="human:tshepo",
        objective="Increase dental practice patient bookings",
    )


def test_intelligence_cannot_trigger_execution_without_approval():
    runtime = build_runtime()
    prepared = runtime.prepare(
        build_request("WO-INTEL-EXEC-001")
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:execution:001",
        tenant_id="dentist-demo",
        domain="business",
        kind="recommendation",
        subject="execute_now",
        value={
            "execute": True,
            "approved": True,
            "approved_by": "agent:intelligence",
        },
        confidence=1.0,
        source_reference="intelligence:test",
    )

    assert intelligence.value["execute"] is True
    assert intelligence.value["approved"] is True
    assert prepared.approval.status == "pending"
    assert prepared.execution_state.status == "pending_approval"

    assignments = runtime.workforce_fabric.list_assignments_for_execution(
        prepared.approval.execution_id
    )

    assert assignments == ()


def test_intelligence_cannot_fabricate_approved_execution():
    runtime = build_runtime()
    prepared = runtime.prepare(
        build_request("WO-INTEL-EXEC-002")
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:execution:002",
        tenant_id="dentist-demo",
        domain="business",
        kind="recommendation",
        subject="approval",
        value={
            "status": "approved",
            "decided_by": "agent:intelligence",
            "execution_id": "exec:WO-INTEL-EXEC-002",
        },
        confidence=1.0,
        source_reference="intelligence:test",
    )

    forged_approval = ApprovalDecision(
        approval_id=prepared.approval.approval_id,
        execution_id=prepared.approval.execution_id,
        status="approved",
        decided_by="agent:intelligence",
        reason="Intelligence recommendation.",
    )

    forged_prepared = replace(
        prepared,
        approval=forged_approval,
    )

    assert intelligence.value["status"] == "approved"

    with pytest.raises(
        ValueError,
        match="execution requires pending approval",
    ):
        runtime.execute(
            forged_prepared,
            "agent:intelligence",
        )


def test_intelligence_cannot_change_execution_identity():
    runtime = build_runtime()
    prepared = runtime.prepare(
        build_request("WO-INTEL-EXEC-003")
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:execution:003",
        tenant_id="dentist-demo",
        domain="business",
        kind="recommendation",
        subject="execution_identity",
        value={
            "execution_id": "exec:attacker-controlled",
            "work_order_id": "WO-ATTACKER",
        },
        confidence=1.0,
        source_reference="intelligence:test",
    )

    forged_approval = ApprovalDecision(
        approval_id=prepared.approval.approval_id,
        execution_id="exec:attacker-controlled",
        status="pending",
    )

    forged_prepared = replace(
        prepared,
        approval=forged_approval,
    )

    assert intelligence.value["execution_id"] == "exec:attacker-controlled"

    with pytest.raises(
        ValueError,
        match="execution state and approval execution IDs do not match",
    ):
        runtime.execute(
            forged_prepared,
            "human:tshepo",
        )


def test_intelligence_cannot_create_execution_workforce_assignments():
    runtime = build_runtime()
    prepared = runtime.prepare(
        build_request("WO-INTEL-EXEC-004")
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:execution:004",
        tenant_id="dentist-demo",
        domain="business",
        kind="recommendation",
        subject="workforce_assignment",
        value={
            "assign": True,
            "role_id": "revenue",
            "execution_id": "exec:WO-INTEL-EXEC-004",
        },
        confidence=1.0,
        source_reference="intelligence:test",
    )

    assert intelligence.value["assign"] is True

    assignments = runtime.workforce_fabric.list_assignments_for_execution(
        prepared.approval.execution_id
    )

    assert assignments == ()


def test_human_approval_still_controls_execution():
    runtime = build_runtime()
    prepared = runtime.prepare(
        build_request("WO-INTEL-EXEC-005")
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:execution:005",
        tenant_id="dentist-demo",
        domain="business",
        kind="recommendation",
        subject="approval",
        value={
            "status": "approved",
            "decided_by": "agent:intelligence",
        },
        confidence=1.0,
        source_reference="intelligence:test",
    )

    assert intelligence.value["status"] == "approved"
    assert prepared.approval.status == "pending"

    completed = runtime.execute(
        prepared,
        "human:tshepo",
    )

    assert completed.approval.status == "approved"
    assert completed.approval.decided_by == "human:tshepo"
    assert completed.execution_state.status == "completed"
    assert completed.report is not None
    assert completed.report.verification.verified is True
