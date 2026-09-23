from dataclasses import dataclass

import pytest

from mananze_os.intelligence_fabric import (
    IntelligenceFabric,
    IntelligenceObservation,
)
from mananze_os.intelligence_provider import (
    IntelligenceCoordinator,
    IntelligenceProviderRegistry,
)


@dataclass(frozen=True)
class DemoProvider:
    provider_id: str = "demo:business"
    domains: tuple[str, ...] = ("business",)

    def observe(
        self,
        *,
        tenant_id: str,
        context: object | None = None,
    ) -> tuple[IntelligenceObservation, ...]:
        return (
            IntelligenceObservation(
                observation_id=f"{self.provider_id}:{tenant_id}:001",
                tenant_id=tenant_id,
                domain="business",
                kind="fact",
                subject="business.revenue",
                value={"amount": 10000, "currency": "ZAR"},
                confidence=0.95,
                source_reference="demo:source",
            ),
        )


@dataclass(frozen=True)
class OperationsProvider:
    provider_id: str = "demo:operations"
    domains: tuple[str, ...] = ("operations",)

    def observe(
        self,
        *,
        tenant_id: str,
        context: object | None = None,
    ) -> tuple[IntelligenceObservation, ...]:
        return ()


@dataclass(frozen=True)
class CrossTenantProvider:
    provider_id: str = "demo:unsafe"
    domains: tuple[str, ...] = ("business",)

    def observe(
        self,
        *,
        tenant_id: str,
        context: object | None = None,
    ) -> tuple[IntelligenceObservation, ...]:
        return (
            IntelligenceObservation(
                observation_id="unsafe:001",
                tenant_id="different-tenant",
                domain="business",
                kind="fact",
                subject="business.revenue",
                value={"amount": 999999},
                confidence=0.9,
            ),
        )


def test_provider_registers_and_can_be_retrieved() -> None:
    registry = IntelligenceProviderRegistry()
    provider = DemoProvider()

    registry.register(provider)

    assert registry.get("demo:business") is provider
    assert registry.list_all() == (provider,)


def test_duplicate_provider_ids_are_rejected() -> None:
    registry = IntelligenceProviderRegistry()
    registry.register(DemoProvider())

    with pytest.raises(ValueError):
        registry.register(DemoProvider())


def test_providers_can_be_selected_by_domain() -> None:
    registry = IntelligenceProviderRegistry()

    business = DemoProvider()
    operations = OperationsProvider()

    registry.register(business)
    registry.register(operations)

    assert registry.providers_for_domain("business") == (business,)
    assert registry.providers_for_domain("operations") == (operations,)
    assert registry.providers_for_domain("unknown") == ()


def test_coordinator_collects_and_publishes_observations() -> None:
    fabric = IntelligenceFabric()
    registry = IntelligenceProviderRegistry()
    registry.register(DemoProvider())

    coordinator = IntelligenceCoordinator(fabric, registry)

    observations = coordinator.collect(
        provider_id="demo:business",
        tenant_id="tenant-a",
    )

    assert len(observations) == 1
    assert fabric.get(
        observations[0].observation_id,
        tenant_id="tenant-a",
    ) == observations[0]


def test_coordinator_preserves_tenant_boundary() -> None:
    fabric = IntelligenceFabric()
    registry = IntelligenceProviderRegistry()
    registry.register(DemoProvider())

    coordinator = IntelligenceCoordinator(fabric, registry)

    observations = coordinator.collect(
        provider_id="demo:business",
        tenant_id="tenant-a",
    )

    assert observations[0].tenant_id == "tenant-a"
    assert fabric.query(
        __import__(
            "mananze_os.intelligence_fabric",
            fromlist=["IntelligenceQuery"],
        ).IntelligenceQuery(tenant_id="tenant-a")
    ) == observations


def test_cross_tenant_provider_output_is_rejected() -> None:
    fabric = IntelligenceFabric()
    registry = IntelligenceProviderRegistry()
    registry.register(CrossTenantProvider())

    coordinator = IntelligenceCoordinator(fabric, registry)

    with pytest.raises(PermissionError):
        coordinator.collect(
            provider_id="demo:unsafe",
            tenant_id="tenant-a",
        )

    assert fabric.list_tenant("tenant-a") == ()


def test_unknown_provider_is_rejected() -> None:
    registry = IntelligenceProviderRegistry()

    with pytest.raises(KeyError):
        registry.get("does-not-exist")


def test_provider_domain_contract_is_preserved() -> None:
    provider = DemoProvider()

    assert provider.provider_id == "demo:business"
    assert provider.domains == ("business",)
