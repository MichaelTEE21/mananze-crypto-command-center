from mananze_os.obligation_intelligence import (
    Obligation,
    ObligationDependency,
)
from mananze_os.obligation_registry import ObligationRegistry


def make_obligation(
    obligation_id: str,
    tenant_id: str,
    name: str = "Internet Service",
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
        status="active",
    )


def test_registry_registers_and_retrieves_obligation():
    registry = ObligationRegistry()
    obligation = make_obligation("OBL-001", "tenant-a")

    registry.register(obligation)

    assert registry.get("OBL-001") == obligation


def test_registry_rejects_duplicate_obligation():
    registry = ObligationRegistry()
    obligation = make_obligation("OBL-001", "tenant-a")

    registry.register(obligation)

    try:
        registry.register(obligation)
        assert False, "expected duplicate obligation rejection"
    except ValueError as exc:
        assert "already registered" in str(exc)


def test_registry_lists_only_requested_tenant():
    registry = ObligationRegistry()

    registry.register(make_obligation("OBL-A", "tenant-a"))
    registry.register(make_obligation("OBL-B", "tenant-b"))

    obligations = registry.list_for_tenant("tenant-a")

    assert [item.obligation_id for item in obligations] == ["OBL-A"]


def test_registry_rejects_empty_tenant():
    registry = ObligationRegistry()

    try:
        registry.list_for_tenant("")
        assert False, "expected tenant validation"
    except ValueError as exc:
        assert "tenant_id is required" in str(exc)


def test_registry_registers_dependency_for_existing_obligation():
    registry = ObligationRegistry()

    obligation = make_obligation("OBL-001", "tenant-a")
    registry.register(obligation)

    dependency = ObligationDependency(
        dependency_id="DEP-001",
        tenant_id="tenant-a",
        obligation_id="OBL-001",
        depends_on="internet connectivity",
        impact="Dispatch and customer communication depend on connectivity",
    )

    registry.register_dependency(dependency)

    dependencies = registry.list_dependencies_for_obligation(
        "OBL-001"
    )

    assert dependencies == (dependency,)


def test_registry_rejects_dependency_for_unknown_obligation():
    registry = ObligationRegistry()

    dependency = ObligationDependency(
        dependency_id="DEP-001",
        tenant_id="tenant-a",
        obligation_id="OBL-MISSING",
        depends_on="internet connectivity",
        impact="Operations depend on connectivity",
    )

    try:
        registry.register_dependency(dependency)
        assert False, "expected unknown obligation rejection"
    except KeyError as exc:
        assert "unknown obligation" in str(exc)


def test_registry_rejects_cross_tenant_dependency():
    registry = ObligationRegistry()

    registry.register(
        make_obligation("OBL-001", "tenant-a")
    )

    dependency = ObligationDependency(
        dependency_id="DEP-001",
        tenant_id="tenant-b",
        obligation_id="OBL-001",
        depends_on="internet connectivity",
        impact="Operations depend on connectivity",
    )

    try:
        registry.register_dependency(dependency)
        assert False, "expected tenant mismatch rejection"
    except ValueError as exc:
        assert "tenant does not match" in str(exc)
