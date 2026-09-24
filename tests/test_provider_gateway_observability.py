from dataclasses import dataclass

import pytest

from mananze_os.provider import ProviderRequest, ProviderResponse
from mananze_os.provider_gateway import ProviderExecutionGateway
from mananze_os.provider_observability import (
    ProviderHealthRegistry,
    ProviderUsageLedger,
)
from mananze_os.provider_registry import ProviderRegistry
from mananze_os.tool_registry import ToolDefinition, ToolRegistry


@dataclass
class RecordingProvider:
    provider_id: str = "provider:test"

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider_id=request.provider_id,
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            success=True,
            output={"status": "ok"},
            usage={"tokens": 123},
            cost=1.75,
            cost_currency="ZAR",
        )


@dataclass
class FailingProvider:
    provider_id: str = "provider:failing"

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        raise RuntimeError("provider unavailable")


def make_gateway(provider):
    tool_registry = ToolRegistry()
    tool_registry.register(
        ToolDefinition(
            tool_id="tool:test",
            version="1.0.0",
            description="test tool",
            capability_id="cap:test",
            input_schema={},
            output_schema={},
            allowed_provider_ids=(provider.provider_id,),
        )
    )

    provider_registry = ProviderRegistry()
    provider_registry.register(provider)

    health = ProviderHealthRegistry()
    ledger = ProviderUsageLedger()

    gateway = ProviderExecutionGateway(
        tool_registry,
        provider_registry,
        health_registry=health,
        usage_ledger=ledger,
    )

    return gateway, health, ledger


def test_gateway_records_success_health_and_cost():
    gateway, health, ledger = make_gateway(RecordingProvider())

    result = gateway.execute(
        provider_id="provider:test",
        tool_id="tool:test",
        tenant_id="tenant:a",
        execution_id="exec:1",
        operation="test",
        payload={"value": 42},
    )

    assert result.success is True

    snapshot = health.get("provider:test")

    assert snapshot.total_requests == 1
    assert snapshot.successful_requests == 1
    assert snapshot.failed_requests == 0
    assert snapshot.last_latency_ms is not None

    records = ledger.list_all()

    assert len(records) == 1
    assert records[0].tenant_id == "tenant:a"
    assert records[0].execution_id == "exec:1"
    assert records[0].usage == {"tokens": 123}
    assert records[0].cost == 1.75
    assert records[0].cost_currency == "ZAR"


def test_gateway_records_provider_exception_as_failure():
    gateway, health, ledger = make_gateway(FailingProvider())

    with pytest.raises(RuntimeError, match="provider unavailable"):
        gateway.execute(
            provider_id="provider:failing",
            tool_id="tool:test",
            tenant_id="tenant:a",
            execution_id="exec:2",
            operation="test",
            payload={},
        )

    snapshot = health.get("provider:failing")

    assert snapshot.total_requests == 1
    assert snapshot.successful_requests == 0
    assert snapshot.failed_requests == 1
    assert snapshot.consecutive_failures == 1

    records = ledger.list_all()

    assert len(records) == 1
    assert records[0].success is False
    assert records[0].tenant_id == "tenant:a"
    assert records[0].execution_id == "exec:2"
    assert records[0].cost == 0.0


def test_gateway_does_not_record_rejected_request():
    gateway, health, ledger = make_gateway(RecordingProvider())

    with pytest.raises(PermissionError):
        gateway.execute(
            provider_id="provider:wrong",
            tool_id="tool:test",
            tenant_id="tenant:a",
            execution_id="exec:3",
            operation="test",
            payload={},
        )

    assert health.get("provider:wrong").total_requests == 0
    assert ledger.list_all() == ()
