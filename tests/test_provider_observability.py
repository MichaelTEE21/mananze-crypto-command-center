from mananze_os.provider_observability import (
    ProviderHealthRegistry,
    ProviderUsageLedger,
)


def test_health_registry_tracks_success_and_failure():
    registry = ProviderHealthRegistry()

    registry.record(
        provider_id="provider:a",
        success=True,
        latency_ms=100,
        recorded_at="2026-01-01T00:00:00+00:00",
    )
    registry.record(
        provider_id="provider:a",
        success=False,
        latency_ms=200,
        recorded_at="2026-01-01T00:01:00+00:00",
    )

    snapshot = registry.get("provider:a")

    assert snapshot.total_requests == 2
    assert snapshot.successful_requests == 1
    assert snapshot.failed_requests == 1
    assert snapshot.consecutive_failures == 1
    assert snapshot.failure_rate == 0.5
    assert snapshot.average_latency_ms == 150
    assert snapshot.last_latency_ms == 200


def test_success_resets_consecutive_failures():
    registry = ProviderHealthRegistry()

    registry.record(
        provider_id="provider:a",
        success=False,
        latency_ms=100,
    )
    registry.record(
        provider_id="provider:a",
        success=False,
        latency_ms=100,
    )
    registry.record(
        provider_id="provider:a",
        success=True,
        latency_ms=100,
    )

    snapshot = registry.get("provider:a")

    assert snapshot.consecutive_failures == 0
    assert snapshot.failed_requests == 2
    assert snapshot.successful_requests == 1


def test_unknown_provider_has_zero_health():
    registry = ProviderHealthRegistry()

    snapshot = registry.get("provider:unknown")

    assert snapshot.total_requests == 0
    assert snapshot.failure_rate == 0.0
    assert snapshot.average_latency_ms == 0.0


def test_usage_ledger_records_execution():
    ledger = ProviderUsageLedger()

    record = ledger.record(
        provider_id="provider:a",
        tool_id="tool:test",
        tenant_id="tenant:a",
        execution_id="exec:1",
        success=True,
        latency_ms=125,
        usage={"tokens": 500},
        cost=2.50,
        cost_currency="ZAR",
        recorded_at="2026-01-01T00:00:00+00:00",
    )

    assert record.provider_id == "provider:a"
    assert record.tool_id == "tool:test"
    assert record.tenant_id == "tenant:a"
    assert record.execution_id == "exec:1"
    assert record.usage == {"tokens": 500}
    assert record.cost == 2.50


def test_usage_ledger_filters_cost():
    ledger = ProviderUsageLedger()

    ledger.record(
        provider_id="provider:a",
        tool_id="tool:test",
        tenant_id="tenant:a",
        execution_id="exec:1",
        success=True,
        latency_ms=100,
        usage={"tokens": 100},
        cost=2.0,
        cost_currency="ZAR",
    )
    ledger.record(
        provider_id="provider:b",
        tool_id="tool:test",
        tenant_id="tenant:a",
        execution_id="exec:2",
        success=True,
        latency_ms=100,
        usage={"tokens": 200},
        cost=3.0,
        cost_currency="ZAR",
    )
    ledger.record(
        provider_id="provider:a",
        tool_id="tool:other",
        tenant_id="tenant:b",
        execution_id="exec:3",
        success=True,
        latency_ms=100,
        usage={"tokens": 300},
        cost=10.0,
        cost_currency="USD",
    )

    assert ledger.total_cost() == 5.0
    assert ledger.total_cost(provider_id="provider:a") == 2.0
    assert ledger.total_cost(tenant_id="tenant:a") == 5.0
    assert ledger.total_cost(tool_id="tool:test") == 5.0
    assert ledger.total_cost(cost_currency="USD") == 10.0


def test_usage_ledger_preserves_all_records():
    ledger = ProviderUsageLedger()

    for index in range(3):
        ledger.record(
            provider_id="provider:a",
            tool_id="tool:test",
            tenant_id="tenant:a",
            execution_id=f"exec:{index}",
            success=True,
            latency_ms=100,
            usage=None,
            cost=1.0,
            cost_currency="ZAR",
        )

    assert len(ledger.list_all()) == 3
