from __future__ import annotations

from dataclasses import replace

import pytest

from mananze_os.approval import ApprovalDecision
from mananze_os.authority import Authority
from mananze_os.authorization import CapabilityPermission
from mananze_os.capability_activation import (
    CapabilityActivation,
    CapabilityActivationPlan,
)
from mananze_os.capability_workforce_bridge import CapabilityWorkforceBridge
from mananze_os.governed_execution import GovernedExecutionController
from mananze_os.governed_provider_execution import (
    GovernedProviderExecutionBoundary,
)
from mananze_os.provider import ProviderResponse
from mananze_os.provider_gateway import ProviderExecutionGateway
from mananze_os.provider_registry import ProviderRegistry
from mananze_os.provider_router import ProviderRoute, ProviderRouter
from mananze_os.runtime import RuntimeExecutionBoundary
from mananze_os.tenant import Tenant
from mananze_os.tool_registry import ToolDefinition, ToolRegistry


TOOL_ID = "mananze:test:controlled"


class FakeProvider:
    provider_id = "test.provider"

    def execute(self, request):
        return ProviderResponse(
            provider_id=self.provider_id,
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            success=True,
            output={
                "status": "executed",
                "operation": request.operation,
                "payload": request.payload,
            },
            usage={"requests": 1},
            cost=1.25,
            cost_currency="ZAR",
        )


def build_provider_boundary():
    tools = ToolRegistry()
    providers = ProviderRegistry()

    provider = FakeProvider()
    providers.register(provider)

    tools.register(
        ToolDefinition(
            tool_id=TOOL_ID,
            version="1.0.0",
            description="Controlled provider test tool",
            capability_id="marketing",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            supported_tenant_ids=("tenant-test",),
            allowed_provider_ids=(provider.provider_id,),
            estimated_cost=1.0,
            cost_currency="ZAR",
            timeout_seconds=30.0,
            max_attempts=1,
            execution_mode="external",
            audit_required=True,
            requires_approval=False,
        )
    )

    gateway = ProviderExecutionGateway(
        tool_registry=tools,
        provider_registry=providers,
    )

    router = ProviderRouter(
        tool_registry=tools,
        provider_registry=providers,
        gateway=gateway,
        routes=(
            ProviderRoute(
                tool_id=TOOL_ID,
                primary_provider_id=provider.provider_id,
            ),
        ),
    )

    runtime_boundary = RuntimeExecutionBoundary(router)

    return GovernedProviderExecutionBoundary(runtime_boundary)


def build_governed_result():
    tenant = Tenant("tenant-test", "Test Tenant")

    authority = Authority(
        actor_id="human:tshepo",
        level="human",
        can_execute=True,
        requires_approval=False,
    )

    permissions = (
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-test",
            capability_id="marketing",
            allowed=True,
        ),
    )

    activation_plan = CapabilityActivationPlan(
        tenant_id="tenant-test",
        twin_id="twin:test",
        activations=(
            CapabilityActivation(
                capability_id="marketing",
                status="active",
                reason="Marketing capability supported by the business twin",
                supporting_truth_ids=("truth:test-marketing",),
            ),
        ),
    )

    bridge = CapabilityWorkforceBridge()

    plan = bridge.build(
        activation_plan=activation_plan,
        work_order_id="wo:test-provider",
        objective="Create a marketing campaign plan",
    )

    # CapabilityWorkforceBridge deliberately does not choose tools.
    # Bind the explicitly selected tool to the execution node for this
    # provider-boundary test.
    node = plan.execution_graph.nodes[0]

    bound_node = replace(
        node,
        tool_id=TOOL_ID,
    )

    bound_graph = replace(
        plan.execution_graph,
        nodes=(bound_node,),
    )

    bound_plan = replace(
        plan,
        execution_graph=bound_graph,
    )

    controller = GovernedExecutionController()

    result = controller.evaluate(
        plan=bound_plan,
        execution_id="exec:wo:test-provider",
        task_id="task:wo:test-provider",
        actor_id="human:tshepo",
        capability_id="marketing",
        action="controlled_execution",
        authority=authority,
        tenant=tenant,
        permissions=permissions,
        tool_id=TOOL_ID,
        payload={
            "objective": "Create a marketing campaign plan",
        },
        risk="low",
    )

    return result


def test_boundary_requires_allowed_governance():
    boundary = build_provider_boundary()
    result = build_governed_result()

    denied = replace(
        result,
        disposition="denied",
        reasons=("denied by test",),
    )

    with pytest.raises(PermissionError, match="allowed governance"):
        boundary.execute(denied)


def test_boundary_requires_action_request():
    boundary = build_provider_boundary()
    result = build_governed_result()

    missing_action = replace(
        result,
        action_request=None,
    )

    with pytest.raises(ValueError, match="action request"):
        boundary.execute(missing_action)


def test_boundary_rejects_execution_identity_mismatch():
    boundary = build_provider_boundary()
    result = build_governed_result()

    bad_request = replace(
        result.action_request,
        execution_id="exec:wrong",
    )

    bad_result = replace(
        result,
        action_request=bad_request,
    )

    with pytest.raises(ValueError, match="execution"):
        boundary.execute(bad_result)


def test_boundary_rejects_tenant_identity_mismatch():
    boundary = build_provider_boundary()
    result = build_governed_result()

    bad_request = replace(
        result.action_request,
        tenant_id="tenant-other",
    )

    bad_result = replace(
        result,
        action_request=bad_request,
    )

    with pytest.raises(ValueError, match="tenant"):
        boundary.execute(bad_result)


def test_boundary_rejects_capability_identity_mismatch():
    boundary = build_provider_boundary()
    result = build_governed_result()

    bad_request = replace(
        result.action_request,
        capability_id="sales",
    )

    bad_result = replace(
        result,
        action_request=bad_request,
    )

    with pytest.raises(ValueError, match="capability"):
        boundary.execute(bad_result)


def test_boundary_rejects_action_identity_mismatch():
    boundary = build_provider_boundary()
    result = build_governed_result()

    bad_request = replace(
        result.action_request,
        action="different_action",
    )

    bad_result = replace(
        result,
        action_request=bad_request,
    )

    with pytest.raises(ValueError, match="action"):
        boundary.execute(bad_result)


def test_boundary_reaches_provider_only_after_governance():
    boundary = build_provider_boundary()
    result = build_governed_result()

    assert result.allowed is True
    assert result.action_request is not None

    executed = boundary.execute(result)

    assert executed.success is True
    assert executed.provider.success is True
    assert executed.provider.provider_id == "test.provider"
    assert executed.provider.tool_id == TOOL_ID
    assert executed.provider.tenant_id == "tenant-test"
    assert executed.provider.execution_id == "exec:wo:test-provider"
    assert executed.provider.cost == 1.25


def test_boundary_preserves_payload():
    boundary = build_provider_boundary()
    result = build_governed_result()

    payload = {
        "objective": "Create a marketing campaign plan",
        "customer": "example-client",
        "test": True,
    }

    executed = boundary.execute(
        replace(
            result,
            action_request=replace(
                result.action_request,
                payload=payload,
            ),
        )
    )

    assert executed.success is True
    assert executed.provider.output["payload"] == payload


def test_boundary_rejects_pending_approval():
    boundary = build_provider_boundary()
    result = build_governed_result()

    pending = replace(
        result,
        disposition="approval_required",
    )

    with pytest.raises(PermissionError):
        boundary.execute(pending)


def test_boundary_rejects_non_approved_approval():
    boundary = build_provider_boundary()
    result = build_governed_result()

    pending = ApprovalDecision(
        approval_id="approval:test",
        execution_id=result.execution_id,
        status="pending",
    )

    pending_result = replace(
        result,
        approval=pending,
    )

    with pytest.raises(
        PermissionError,
        match="non-approved",
    ):
        boundary.execute(pending_result)


