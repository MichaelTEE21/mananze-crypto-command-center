from mananze_os.intelligence_fabric import IntelligenceFabric, IntelligenceQuery
from mananze_os.intelligence_provider import IntelligenceCoordinator, IntelligenceProviderRegistry
from mananze_os.obligation_intelligence import Obligation
from mananze_os.obligation_intelligence_provider import ObligationIntelligenceProvider
from mananze_os.obligation_registry import ObligationRegistry


def make_obligation(
    obligation_id: str,
    tenant_id: str,
    name: str = "Monthly Internet",
) -> Obligation:
    return Obligation(
        obligation_id=obligation_id,
        tenant_id=tenant_id,
        name=name,
        obligation_type="service",
        counterparty="InternetCo",
        amount=1000,
        currency="ZAR",
        frequency="monthly",
        due_date="2026-10-01",
        status="active",
        approval_required=True,
        source_reference="invoice-001",
    )


def test_provider_reads_registry_and_emits_verified_observation() -> None:
    registry = ObligationRegistry()
    registry.register(make_obligation("OBL-001", "tenant-a"))

    provider = ObligationIntelligenceProvider(registry)

    observations = provider.observe(tenant_id="tenant-a")

    assert len(observations) == 1

    observation = observations[0]

    assert observation.observation_id == "obligation:OBL-001"
    assert observation.tenant_id == "tenant-a"
    assert observation.domain == "obligations"
    assert observation.kind == "fact"
    assert observation.status == "verified"
    assert observation.confidence == 1.0
    assert observation.source_reference == "invoice-001"
    assert observation.value["counterparty"] == "InternetCo"
    assert observation.value["amount"] == 1000
    assert observation.value["currency"] == "ZAR"


def test_provider_is_tenant_scoped() -> None:
    registry = ObligationRegistry()
    registry.register(make_obligation("OBL-A", "tenant-a"))
    registry.register(make_obligation("OBL-B", "tenant-b"))

    provider = ObligationIntelligenceProvider(registry)

    observations = provider.observe(tenant_id="tenant-a")

    assert [item.tenant_id for item in observations] == ["tenant-a"]
    assert [item.observation_id for item in observations] == [
        "obligation:OBL-A"
    ]


def test_provider_rejects_empty_tenant() -> None:
    provider = ObligationIntelligenceProvider(ObligationRegistry())

    try:
        provider.observe(tenant_id="")
        assert False, "expected tenant validation"
    except ValueError as exc:
        assert "tenant_id is required" in str(exc)


def test_provider_does_not_modify_authoritative_registry() -> None:
    registry = ObligationRegistry()
    obligation = make_obligation("OBL-001", "tenant-a")
    registry.register(obligation)

    provider = ObligationIntelligenceProvider(registry)

    provider.observe(tenant_id="tenant-a")

    assert registry.get("OBL-001") == obligation


def test_provider_domains_are_explicit() -> None:
    provider = ObligationIntelligenceProvider(ObligationRegistry())

    assert provider.provider_id == "mananze:obligations"
    assert provider.domains == ("obligations", "economic")


def test_provider_integrates_with_coordinator_and_fabric() -> None:
    registry = ObligationRegistry()
    registry.register(make_obligation("OBL-001", "tenant-a"))

    provider = ObligationIntelligenceProvider(registry)

    provider_registry = IntelligenceProviderRegistry()
    provider_registry.register(provider)

    fabric = IntelligenceFabric()
    coordinator = IntelligenceCoordinator(fabric, provider_registry)

    observations = coordinator.collect(
        provider_id="mananze:obligations",
        tenant_id="tenant-a",
    )

    assert len(observations) == 1

    stored = fabric.get(
        "obligation:OBL-001",
        tenant_id="tenant-a",
    )

    assert stored == observations[0]


def test_coordinator_preserves_tenant_boundary() -> None:
    registry = ObligationRegistry()
    registry.register(make_obligation("OBL-A", "tenant-a"))

    provider = ObligationIntelligenceProvider(registry)
    provider_registry = IntelligenceProviderRegistry()
    provider_registry.register(provider)

    fabric = IntelligenceFabric()
    coordinator = IntelligenceCoordinator(fabric, provider_registry)

    coordinator.collect(
        provider_id="mananze:obligations",
        tenant_id="tenant-a",
    )

    tenant_a = fabric.query(
        IntelligenceQuery(tenant_id="tenant-a")
    )
    tenant_b = fabric.query(
        IntelligenceQuery(tenant_id="tenant-b")
    )

    assert len(tenant_a) == 1
    assert tenant_a[0].observation_id == "obligation:OBL-A"
    assert tenant_b == ()


def test_provider_does_not_create_obligations() -> None:
    registry = ObligationRegistry()
    registry.register(make_obligation("OBL-001", "tenant-a"))

    provider = ObligationIntelligenceProvider(registry)

    provider.observe(tenant_id="tenant-a")

    assert len(registry.list_all()) == 1
