from mananze_os.authority import Authority
from mananze_os.input_request import InputRequest
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
    "operations",
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


def test_prepare_returns_request_in_waiting_approval():
    runtime = build_runtime()

    prepared = runtime.prepare(
        build_request("req-lifecycle-prepare")
    )

    assert prepared.request_state.request_id == "req-lifecycle-prepare"
    assert prepared.request_state.status == "waiting_approval"
    assert prepared.execution_state.status == "pending_approval"


def test_execute_completes_request_after_execution_verification():
    runtime = build_runtime()

    prepared = runtime.prepare(
        build_request("req-lifecycle-execute")
    )

    result = runtime.execute(
        prepared,
        approved_by="human:tshepo",
    )

    assert result.request_state.request_id == "req-lifecycle-execute"
    assert result.request_state.status == "completed"
    assert result.execution_state.status == "completed"
    assert result.report is not None
    assert result.report.verification.verified is True


def test_request_lifecycle_does_not_replace_execution_lifecycle():
    runtime = build_runtime()

    prepared = runtime.prepare(
        build_request("req-lifecycle-boundary")
    )

    assert prepared.request_state.status == "waiting_approval"
    assert prepared.execution_state.status == "pending_approval"

    result = runtime.execute(
        prepared,
        approved_by="human:tshepo",
    )

    assert result.request_state.status == "completed"
    assert result.execution_state.status == "completed"
