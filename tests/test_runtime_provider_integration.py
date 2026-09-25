from dataclasses import dataclass

from mananze_os.provider import ProviderRequest, ProviderResponse
from mananze_os.mananze_workforce_catalog import build_mananze_workforce
from mananze_os.provider_gateway import ProviderExecutionGateway
from mananze_os.provider_observability import (
    ProviderHealthRegistry,
    ProviderUsageLedger,
)
from mananze_os.provider_registry import ProviderRegistry
from mananze_os.provider_router import ProviderRoute, ProviderRouter
from mananze_os.runtime import (
    ExecutionRequest,
    RuntimeExecutionBoundary,
)
from mananze_os.tool_registry import ToolDefinition, ToolRegistry


@dataclass
class FakeProvider:
    provider_id: str = "test.provider"

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider_id=self.provider_id,
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            success=True,
            output={
                "status": "executed",
                "operation": request.operation,
            },
            usage={
                "requests": 1,
                "test": True,
            },
            cost=1.25,
            cost_currency="ZAR",
        )


def build_boundary():
    tool_registry = ToolRegistry()

    tool_registry.register(
        ToolDefinition(
            tool_id="mananze:controlled_execution",
            version="1.0.0",
            description="Controlled provider execution integration test",
            capability_id="controlled_execution",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            allowed_provider_ids=("test.provider",),
            execution_mode="external",
            audit_required=True,
            requires_approval=True,
        )
    )

    provider_registry = ProviderRegistry()
    provider_registry.register(FakeProvider())

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
                tool_id="mananze:controlled_execution",
                primary_provider_id="test.provider",
            ),
        ),
    )

    boundary = RuntimeExecutionBoundary(router)

    return boundary, health, usage


def test_runtime_execution_boundary_reaches_provider_gateway():
    boundary, health, usage = build_boundary()

    result = boundary.execute(
        ExecutionRequest(
            tenant_id="tenant-test",
            execution_id="exec-test-001",
            tool_id="mananze:controlled_execution",
            operation="controlled_execution",
            payload={
                "work_order_id": "wo-test-001",
                "execution_id": "exec-test-001",
            },
            authorization_id="authorization:exec-test-001",
            approval_id="approval-test-001",
        )
    )

    assert result.success is True
    assert result.provider_id == "test.provider"
    assert result.tool_id == "mananze:controlled_execution"
    assert result.tenant_id == "tenant-test"
    assert result.execution_id == "exec-test-001"
    assert result.cost == 1.25
    assert result.cost_currency == "ZAR"

    snapshot = health.get("test.provider")

    assert snapshot.total_requests == 1
    assert snapshot.successful_requests == 1
    assert snapshot.failed_requests == 0

    assert usage.total_cost(
        provider_id="test.provider",
        tenant_id="tenant-test",
        tool_id="mananze:controlled_execution",
        cost_currency="ZAR",
    ) == 1.25
def test_runtime_execution_boundary_preserves_tool_payload_and_provider_result():
    boundary, health, usage = build_boundary()

    result = boundary.execute(
        ExecutionRequest(
            tenant_id="tenant-test",
            execution_id="exec-test-002",
            tool_id="mananze:controlled_execution",
            operation="controlled_execution",
            payload={
                "work_order_id": "wo-test-002",
                "execution_id": "exec-test-002",
                "assignment_id": "assignment-test-002",
                "node_id": "node-test-002",
                "role_id": "role-test",
                "capability_id": "controlled_execution",
                "skill_ids": ("execution:coordination",),
            },
            authorization_id="authorization:exec-test-002",
            approval_id="approval-test-002",
        )
    )

    assert result.success is True
    assert result.provider_id == "test.provider"
    assert result.cost == 1.25
    assert result.cost_currency == "ZAR"

    snapshot = health.get("test.provider")
    assert snapshot.total_requests == 1
    assert snapshot.successful_requests == 1

    assert usage.total_cost(
        provider_id="test.provider",
        tenant_id="tenant-test",
        tool_id="mananze:controlled_execution",
        cost_currency="ZAR",
    ) == 1.25
def test_mananze_runtime_executes_skill_bound_tool_through_provider_router():
    from mananze_os.authorization import Authority, CapabilityPermission
    from mananze_os.input_gate import InputRequest
    from mananze_os.runtime import MananzeRuntime
    from mananze_os.tenant import Tenant

    tool_registry = MananzeRuntime().tool_registry

    tool = tool_registry.get("mananze:marketing:campaign_plan")

    provider_registry = ProviderRegistry()
    provider_registry.register(FakeProvider())

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
                tool_id="mananze:marketing:campaign_plan",
                primary_provider_id="test.provider",
            ),
            ProviderRoute(
                tool_id="mananze:marketing:content_draft",
                primary_provider_id="test.provider",
            ),
        ),
    )

    runtime = MananzeRuntime(
        tenants=(
            Tenant(
                tenant_id="tenant-test",
                name="Test Tenant",
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
        permissions=(
            CapabilityPermission(
                actor_id="human:tshepo",
                tenant_id="tenant-test",
                capability_id=tool.capability_id,
            ),
        ),
        provider_router=router,
    )

    prepared = runtime.prepare(
        InputRequest(
            request_id="WO-PROVIDER-E2E-001",
            tenant_id="tenant-test",
            actor_id="human:tshepo",
            objective="Create a campaign plan for the business",
            candidate_capability_ids=(tool.capability_id,),
        )
    )

    completed = runtime.execute(
        prepared,
        "human:tshepo",
    )

    assert completed.report is not None
    assert completed.report.status == "completed"

    provider_evidence = tuple(
        item
        for item in completed.report.evidence
        if item.action == "node_execution"
        and "provider_id=test.provider" in item.details
    )

    assert provider_evidence
    assert any(
        f"tool_id={tool.tool_id}" in item.details
        for item in provider_evidence
    )

    assert usage.total_cost(
        provider_id="test.provider",
        tenant_id="tenant-test",
        tool_id=tool.tool_id,
        cost_currency="ZAR",
    ) == 1.25




