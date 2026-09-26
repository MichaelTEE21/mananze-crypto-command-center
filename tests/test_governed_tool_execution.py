from dataclasses import dataclass

import pytest

from mananze_os.action_gate import ActionRequest
from mananze_os.governed_execution import GovernedExecutionResult
from mananze_os.governed_provider_execution import (
    GovernedProviderExecutionBoundary,
)
from mananze_os.provider import ProviderRequest, ProviderResponse
from mananze_os.provider_gateway import ProviderExecutionGateway
from mananze_os.provider_observability import (
    ProviderHealthRegistry,
    ProviderUsageLedger,
)
from mananze_os.provider_registry import ProviderRegistry
from mananze_os.provider_router import ProviderRoute, ProviderRouter
from mananze_os.runtime import RuntimeExecutionBoundary
from mananze_os.tool_registry import ToolDefinition, ToolRegistry
from mananze_os.tool_selection import ToolBinding, ToolBindingPlan
from mananze_os.governed_tool_execution import (
    GovernedToolExecutionBoundary,
)


@dataclass
class FakeProvider:
    provider_id: str = "test.provider"
    succeed: bool = True

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider_id=self.provider_id,
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            success=self.succeed,
            output={
                "status": "executed" if self.succeed else "failed",
            },
            usage={"requests": 1},
            cost=1.25 if self.succeed else 0.0,
            cost_currency="ZAR",
            error=None if self.succeed else "provider failure",
        )


@dataclass
class FakeExecutionNode:
    node_id: str
    capability_id: str
    tool_id: str | None = None


@dataclass
class FakeExecutionGraph:
    nodes: tuple[FakeExecutionNode, ...]


def make_tool_registry(
    *,
    tool_id="tool-1",
    capability_id="marketing",
    provider_ids=("test.provider",),
    tenant_ids=(),
):
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            tool_id=tool_id,
            version="1.0.0",
            description="Test governed tool",
            capability_id=capability_id,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            supported_skill_ids=("marketing:campaign_planning",),
            supported_tenant_ids=tenant_ids,
            allowed_provider_ids=provider_ids,
            execution_mode="external",
            risk="low",
        )
    )

    return registry


def make_binding(
    *,
    node_id="node-1",
    capability_id="marketing",
    tool_id="tool-1",
    tenant_id="tenant-1",
    provider_ids=("test.provider",),
):
    return ToolBinding(
        node_id=node_id,
        capability_id=capability_id,
        tool_id=tool_id,
        tenant_id=tenant_id,
        execution_mode="external",
        risk="low",
        required_permission_ids=(),
        supported_skill_ids=("marketing:campaign_planning",),
        allowed_provider_ids=provider_ids,
    )


def make_plan(*, binding=None, node_tool_id=None):
    binding = binding or make_binding()

    if node_tool_id is None:
        node_tool_id = binding.tool_id

    return ToolBindingPlan(
        tenant_id=binding.tenant_id,
        twin_id="twin-1",
        work_order_id="wo-1",
        bindings=(binding,),
        execution_graph=FakeExecutionGraph(
            nodes=(
                FakeExecutionNode(
                    node_id=binding.node_id,
                    capability_id=binding.capability_id,
                    tool_id=node_tool_id,
                ),
            )
        ),
    )


def make_governance(
    *,
    execution_id="exec-1",
    tenant_id="tenant-1",
    capability_id="marketing",
    tool_id="tool-1",
    disposition="allowed",
):
    request = ActionRequest(
        action_id="action-1",
        tenant_id=tenant_id,
        execution_id=execution_id,
        task_id="task-1",
        actor_id="human:test",
        tool_id=tool_id,
        capability_id=capability_id,
        action="execute",
        risk="low",
        payload={"work_order_id": "wo-1"},
        requires_approval=False,
    )

    return GovernedExecutionResult(
        execution_id=execution_id,
        tenant_id=tenant_id,
        work_order_id="wo-1",
        task_id="task-1",
        actor_id="human:test",
        capability_id=capability_id,
        action="execute",
        disposition=disposition,
        action_request=request,
    )


def make_boundary(*, provider_succeeds=True):
    tool_registry = make_tool_registry()

    provider_registry = ProviderRegistry()
    provider_registry.register(
        FakeProvider(succeed=provider_succeeds)
    )

    health = ProviderHealthRegistry()
    usage = ProviderUsageLedger()

    gateway = ProviderExecutionGateway(
        tool_registry=tool_registry,
        provider_registry=provider_registry,
        health_registry=health,
        usage_ledger=usage,
    )

    router = ProviderRouter(
        tool_registry=tool_registry,
        provider_registry=provider_registry,
        gateway=gateway,
        routes=(
            ProviderRoute(
                tool_id="tool-1",
                primary_provider_id="test.provider",
            ),
        ),
    )

    runtime_boundary = RuntimeExecutionBoundary(router)

    provider_boundary = GovernedProviderExecutionBoundary(
        runtime_boundary
    )

    boundary = GovernedToolExecutionBoundary(
        tool_registry=tool_registry,
        provider_boundary=provider_boundary,
    )

    return boundary, health, usage


def test_allowed_execution_reaches_provider_gateway():
    boundary, health, usage = make_boundary()

    result = boundary.execute(
        plan=make_plan(),
        governance=make_governance(),
    )

    assert result.success is True
    assert result.binding.tool_id == "tool-1"
    assert result.provider.provider.provider_id == "test.provider"

    snapshot = health.get("test.provider")
    assert snapshot.total_requests == 1
    assert snapshot.successful_requests == 1

    assert usage.total_cost(
        provider_id="test.provider",
        tenant_id="tenant-1",
        tool_id="tool-1",
        cost_currency="ZAR",
    ) == 1.25


def test_unapproved_execution_is_rejected():
    boundary, _, _ = make_boundary()

    with pytest.raises(PermissionError):
        boundary.execute(
            plan=make_plan(),
            governance=make_governance(
                disposition="approval_required"
            ),
        )


def test_tool_binding_must_match_execution_node():
    boundary, _, _ = make_boundary()

    plan = make_plan(node_tool_id="different-tool")

    with pytest.raises(ValueError, match="tool"):
        boundary.execute(
            plan=plan,
            governance=make_governance(),
        )


def test_tenant_lineage_must_match():
    boundary, _, _ = make_boundary()

    with pytest.raises(ValueError, match="tenant"):
        boundary.execute(
            plan=make_plan(),
            governance=make_governance(
                tenant_id="different-tenant"
            ),
        )


def test_capability_lineage_must_match():
    boundary, _, _ = make_boundary()

    with pytest.raises(ValueError, match="capability"):
        boundary.execute(
            plan=make_plan(),
            governance=make_governance(
                capability_id="sales"
            ),
        )


def test_provider_must_be_compatible_with_bound_tool():
    tool_registry = make_tool_registry(
        provider_ids=("allowed.provider",)
    )

    provider_registry = ProviderRegistry()
    provider_registry.register(
        FakeProvider(provider_id="test.provider")
    )

    health = ProviderHealthRegistry()
    usage = ProviderUsageLedger()

    gateway = ProviderExecutionGateway(
        tool_registry=tool_registry,
        provider_registry=provider_registry,
        health_registry=health,
        usage_ledger=usage,
    )

    with pytest.raises(PermissionError, match="not allowed"):
        ProviderRouter(
            tool_registry=tool_registry,
            provider_registry=provider_registry,
            gateway=gateway,
            routes=(
                ProviderRoute(
                    tool_id="tool-1",
                    primary_provider_id="test.provider",
                ),
            ),
        )

def test_unregistered_tool_is_rejected():
    boundary, _, _ = make_boundary()

    binding = make_binding(tool_id="missing-tool")

    plan = make_plan(binding=binding)

    governance = make_governance(tool_id="missing-tool")

    with pytest.raises(LookupError, match="not registered"):
        boundary.execute(
            plan=plan,
            governance=governance,
        )


def test_governance_decision_is_preserved():
    boundary, _, _ = make_boundary()

    governance = make_governance()

    result = boundary.execute(
        plan=make_plan(),
        governance=governance,
    )

    assert result.governance is governance
    assert result.provider.governance is governance


def test_provider_failure_is_not_reported_as_success():
    boundary, _, _ = make_boundary(
        provider_succeeds=False
    )

    result = boundary.execute(
        plan=make_plan(),
        governance=make_governance(),
    )

    assert result.success is False
    assert result.provider.success is False


def test_boundary_cannot_bypass_governance():
    boundary, health, _ = make_boundary()

    governance = make_governance(
        disposition="denied"
    )

    with pytest.raises(PermissionError):
        boundary.execute(
            plan=make_plan(),
            governance=governance,
        )

    snapshot = health.get("test.provider")
    assert snapshot.total_requests == 0


def test_registered_tool_must_match_binding_metadata():
    boundary, _, _ = make_boundary()

    binding = make_binding(
        provider_ids=("different.provider",)
    )

    with pytest.raises(ValueError, match="provider restrictions"):
        boundary.execute(
            plan=make_plan(binding=binding),
            governance=make_governance(),
        )
def test_provider_must_be_compatible_with_bound_tool():
    tool_registry = make_tool_registry(
        provider_ids=("allowed.provider",)
    )

    provider_registry = ProviderRegistry()
    provider_registry.register(
        FakeProvider(provider_id="test.provider")
    )

    health = ProviderHealthRegistry()
    usage = ProviderUsageLedger()

    gateway = ProviderExecutionGateway(
        tool_registry=tool_registry,
        provider_registry=provider_registry,
        health_registry=health,
        usage_ledger=usage,
    )

    with pytest.raises(PermissionError, match="not allowed"):
        ProviderRouter(
            tool_registry=tool_registry,
            provider_registry=provider_registry,
            gateway=gateway,
            routes=(
                ProviderRoute(
                    tool_id="tool-1",
                    primary_provider_id="test.provider",
                ),
            ),
        )



