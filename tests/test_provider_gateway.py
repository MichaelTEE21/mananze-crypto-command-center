from dataclasses import dataclass

import pytest

from mananze_os.provider import ProviderRequest, ProviderResponse
from mananze_os.provider_gateway import ProviderExecutionGateway
from mananze_os.provider_registry import ProviderRegistry
from mananze_os.tool_registry import ToolDefinition, ToolRegistry


@dataclass
class FakeProvider:
    provider_id: str = "provider:test"

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider_id=self.provider_id,
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            success=True,
            output={"result": "ok", "operation": request.operation},
            usage={"requests": 1},
            cost=1.25,
            cost_currency="ZAR",
        )


def build_gateway():
    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Test provider tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            execution_mode="external",
        )
    )

    providers = ProviderRegistry()
    providers.register(FakeProvider())

    return ProviderExecutionGateway(tools, providers)


def test_gateway_executes_through_registered_provider():
    gateway = build_gateway()

    result = gateway.execute(
        provider_id="provider:test",
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="test_operation",
        payload={"hello": "world"},
    )

    assert result.success is True
    assert result.provider_id == "provider:test"
    assert result.tool_id == "tool:test"
    assert result.tenant_id == "tenant:test"
    assert result.execution_id == "exec:test"
    assert result.output["result"] == "ok"
    assert result.cost == 1.25
    assert result.cost_currency == "ZAR"


def test_gateway_rejects_unknown_tool():
    gateway = build_gateway()

    with pytest.raises(KeyError, match="unknown tool"):
        gateway.execute(
            provider_id="provider:test",
            tool_id="tool:missing",
            tenant_id="tenant:test",
            execution_id="exec:test",
            operation="test",
            payload={},
        )


def test_gateway_rejects_unknown_provider():
    gateway = build_gateway()

    with pytest.raises(KeyError, match="unknown provider"):
        gateway.execute(
            provider_id="provider:missing",
            tool_id="tool:test",
            tenant_id="tenant:test",
            execution_id="exec:test",
            operation="test",
            payload={},
        )




def test_gateway_allows_provider_explicitly_allowed_for_tool():
    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Test provider tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            allowed_provider_ids=("provider:test",),
            execution_mode="external",
        )
    )

    providers = ProviderRegistry()
    providers.register(FakeProvider())

    gateway = ProviderExecutionGateway(tools, providers)

    result = gateway.execute(
        provider_id="provider:test",
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="test",
        payload={},
    )

    assert result.success is True


def test_gateway_rejects_provider_not_allowed_for_tool():
    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Test provider tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            allowed_provider_ids=("provider:other",),
            execution_mode="external",
        )
    )

    providers = ProviderRegistry()
    providers.register(FakeProvider())

    gateway = ProviderExecutionGateway(tools, providers)

    with pytest.raises(PermissionError, match="not allowed for tool"):
        gateway.execute(
            provider_id="provider:test",
            tool_id="tool:test",
            tenant_id="tenant:test",
            execution_id="exec:test",
            operation="test",
            payload={},
        )


def test_tool_registry_unrestricted_provider_allows_registered_provider():
    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Test provider tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
    )

    assert tools.supports_provider("tool:test", "provider:any") is True


def test_tool_registry_rejects_invalid_provider_id():
    with pytest.raises(ValueError, match="allowed provider IDs"):
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Test provider tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            allowed_provider_ids=(" ",),
        )


def test_tool_registry_provider_compatibility():
    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Test provider tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            allowed_provider_ids=("provider:a", "provider:b"),
        )
    )

    assert tools.supports_provider("tool:test", "provider:a") is True
    assert tools.supports_provider("tool:test", "provider:b") is True
    assert tools.supports_provider("tool:test", "provider:c") is False

def test_gateway_rejects_cross_tenant_provider_response():
    class CrossTenantProvider(FakeProvider):
        def execute(self, request: ProviderRequest) -> ProviderResponse:
            return ProviderResponse(
                provider_id=self.provider_id,
                tool_id=request.tool_id,
                tenant_id="tenant:other",
                execution_id=request.execution_id,
                success=True,
                output={},
            )

    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Test provider tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            execution_mode="external",
        )
    )

    providers = ProviderRegistry()
    providers.register(CrossTenantProvider())

    gateway = ProviderExecutionGateway(tools, providers)

    with pytest.raises(RuntimeError, match="cross-tenant"):
        gateway.execute(
            provider_id="provider:test",
            tool_id="tool:test",
            tenant_id="tenant:test",
            execution_id="exec:test",
            operation="test",
            payload={},
        )


def test_gateway_rejects_mismatched_execution_id():
    class BadExecutionProvider(FakeProvider):
        def execute(self, request: ProviderRequest) -> ProviderResponse:
            return ProviderResponse(
                provider_id=self.provider_id,
                tool_id=request.tool_id,
                tenant_id=request.tenant_id,
                execution_id="exec:other",
                success=True,
                output={},
            )

    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Test provider tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            execution_mode="external",
        )
    )

    providers = ProviderRegistry()
    providers.register(BadExecutionProvider())

    gateway = ProviderExecutionGateway(tools, providers)

    with pytest.raises(RuntimeError, match="mismatched execution ID"):
        gateway.execute(
            provider_id="provider:test",
            tool_id="tool:test",
            tenant_id="tenant:test",
            execution_id="exec:test",
            operation="test",
            payload={},
        )
