from dataclasses import dataclass, field

import pytest

from mananze_os.provider import ProviderRequest, ProviderResponse
from mananze_os.provider_gateway import ProviderExecutionGateway
from mananze_os.provider_registry import ProviderRegistry
from mananze_os.provider_router import ProviderRoute, ProviderRouter
from mananze_os.tool_registry import ToolDefinition, ToolRegistry


@dataclass
class RecordingProvider:
    provider_id: str
    succeed: bool = True
    calls: list[ProviderRequest] = field(default_factory=list)

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        self.calls.append(request)

        return ProviderResponse(
            provider_id=self.provider_id,
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            success=self.succeed,
            output={"provider": self.provider_id},
            error=None if self.succeed else "provider failed",
            usage={"requests": 1},
            cost=2.0,
            cost_currency="ZAR",
        )


def build_router(
    *,
    allowed_provider_ids=(),
    primary="provider:primary",
    fallbacks=("provider:fallback",),
    primary_succeed=True,
    fallback_succeed=True,
):
    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Router test tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            allowed_provider_ids=allowed_provider_ids,
            execution_mode="external",
        )
    )

    primary_provider = RecordingProvider(
        primary,
        succeed=primary_succeed,
    )
    fallback_provider = RecordingProvider(
        "provider:fallback",
        succeed=fallback_succeed,
    )

    providers = ProviderRegistry()
    providers.register(primary_provider)
    providers.register(fallback_provider)

    gateway = ProviderExecutionGateway(tools, providers)

    router = ProviderRouter(
        tools,
        providers,
        gateway,
        routes=(
            ProviderRoute(
                tool_id="tool:test",
                primary_provider_id=primary,
                fallback_provider_ids=fallbacks,
            ),
        ),
    )

    return router, primary_provider, fallback_provider


def test_primary_provider_executes_successfully():
    router, primary, fallback = build_router()

    result = router.route(
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="quote",
        payload={"item": "cabinet"},
    )

    assert result.success is True
    assert result.provider_id == "provider:primary"
    assert result.attempted_provider_ids == ("provider:primary",)
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 0


def test_primary_failure_uses_configured_fallback():
    router, primary, fallback = build_router(
        primary_succeed=False,
        fallback_succeed=True,
    )

    result = router.route(
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="quote",
        payload={"item": "cabinet"},
    )

    assert result.success is True
    assert result.provider_id == "provider:fallback"
    assert result.attempted_provider_ids == (
        "provider:primary",
        "provider:fallback",
    )
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


def test_unconfigured_registered_provider_is_not_tried():
    router, primary, fallback = build_router(
        primary_succeed=False,
        fallbacks=(),
    )

    result = router.route(
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="quote",
        payload={},
    )

    assert result.success is False
    assert result.attempted_provider_ids == ("provider:primary",)
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 0


def test_disallowed_fallback_cannot_be_registered():
    with pytest.raises(PermissionError, match="not allowed"):
        build_router(
            allowed_provider_ids=("provider:primary",),
        )


def test_duplicate_primary_and_fallback_are_rejected():
    with pytest.raises(ValueError, match="primary provider"):
        ProviderRoute(
            tool_id="tool:test",
            primary_provider_id="provider:primary",
            fallback_provider_ids=("provider:primary",),
        )


def test_duplicate_fallbacks_are_rejected():
    with pytest.raises(ValueError, match="fallback provider IDs must be unique"):
        ProviderRoute(
            tool_id="tool:test",
            primary_provider_id="provider:primary",
            fallback_provider_ids=(
                "provider:fallback",
                "provider:fallback",
            ),
        )


def test_disabled_route_is_rejected():
    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Router test tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
    )

    providers = ProviderRegistry()
    provider = RecordingProvider("provider:primary")
    providers.register(provider)

    gateway = ProviderExecutionGateway(tools, providers)

    router = ProviderRouter(
        tools,
        providers,
        gateway,
        routes=(
            ProviderRoute(
                tool_id="tool:test",
                primary_provider_id="provider:primary",
                enabled=False,
            ),
        ),
    )

    with pytest.raises(PermissionError, match="disabled"):
        router.route(
            tool_id="tool:test",
            tenant_id="tenant:test",
            execution_id="exec:test",
            operation="test",
            payload={},
        )


def test_missing_provider_is_handled_deterministically():
    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Router test tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
    )

    providers = ProviderRegistry()
    fallback = RecordingProvider("provider:fallback")
    providers.register(fallback)

    gateway = ProviderExecutionGateway(tools, providers)

    router = ProviderRouter(
        tools,
        providers,
        gateway,
        routes=(
            ProviderRoute(
                tool_id="tool:test",
                primary_provider_id="provider:missing",
                fallback_provider_ids=("provider:fallback",),
            ),
        ),
    )

    result = router.route(
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="test",
        payload={},
    )

    assert result.success is True
    assert result.provider_id == "provider:fallback"
    assert result.attempted_provider_ids == (
        "provider:missing",
        "provider:fallback",
    )


def test_all_configured_providers_fail_with_controlled_failure():
    router, primary, fallback = build_router(
        primary_succeed=False,
        fallback_succeed=False,
    )

    result = router.route(
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="test",
        payload={},
    )

    assert result.success is False
    assert result.provider_id is None
    assert result.attempted_provider_ids == (
        "provider:primary",
        "provider:fallback",
    )
    assert "all configured providers failed" in result.error
    assert "provider:primary" in result.error
    assert "provider:fallback" in result.error


def test_tenant_and_execution_identity_are_preserved():
    router, primary, _ = build_router()

    result = router.route(
        tool_id="tool:test",
        tenant_id="tenant:abc",
        execution_id="exec:123",
        operation="test",
        payload={},
    )

    assert result.tenant_id == "tenant:abc"
    assert result.execution_id == "exec:123"
    assert primary.calls[0].tenant_id == "tenant:abc"
    assert primary.calls[0].execution_id == "exec:123"


def test_operation_and_payload_are_preserved():
    router, primary, _ = build_router()

    payload = {
        "customer": "ABC Cabinets",
        "dimensions": [600, 720],
    }

    router.route(
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="calculate_quote",
        payload=payload,
    )

    request = primary.calls[0]

    assert request.operation == "calculate_quote"
    assert request.payload == payload


def test_router_delegates_execution_through_gateway():
    class RecordingGateway:
        def __init__(self):
            self.calls = []

        def execute(self, **kwargs):
            self.calls.append(kwargs)
            return type(
                "Result",
                (),
                {
                    "success": True,
                    "provider_id": kwargs["provider_id"],
                    "tool_id": kwargs["tool_id"],
                    "tenant_id": kwargs["tenant_id"],
                    "execution_id": kwargs["execution_id"],
                    "output": {"ok": True},
                    "error": None,
                    "usage": None,
                    "cost": 0.0,
                    "cost_currency": "ZAR",
                },
            )()

    tools = ToolRegistry()
    tools.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="Router test tool",
            capability_id="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
    )

    providers = ProviderRegistry()
    providers.register(RecordingProvider("provider:primary"))

    gateway = RecordingGateway()

    router = ProviderRouter(
        tools,
        providers,
        gateway,
        routes=(
            ProviderRoute(
                tool_id="tool:test",
                primary_provider_id="provider:primary",
            ),
        ),
    )

    result = router.route(
        tool_id="tool:test",
        tenant_id="tenant:test",
        execution_id="exec:test",
        operation="test",
        payload={"x": 1},
    )

    assert result.success is True
    assert len(gateway.calls) == 1
    assert gateway.calls[0]["provider_id"] == "provider:primary"
