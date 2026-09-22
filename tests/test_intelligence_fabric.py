from datetime import datetime, timezone

import pytest

from mananze_os.intelligence_fabric import (
    IntelligenceFabric,
    IntelligenceObservation,
    IntelligenceQuery,
)


def make_observation(
    observation_id: str,
    tenant_id: str = "tenant-a",
    *,
    domain: str = "business",
    kind: str = "fact",
    status: str = "observed",
    confidence: float = 0.9,
) -> IntelligenceObservation:
    return IntelligenceObservation(
        observation_id=observation_id,
        tenant_id=tenant_id,
        domain=domain,
        kind=kind,
        subject="business.revenue",
        value={"amount": 10000, "currency": "ZAR"},
        status=status,
        confidence=confidence,
        source_reference="document:invoice-001",
        observed_at=datetime.now(timezone.utc),
    )


def test_publish_and_get_are_tenant_scoped() -> None:
    fabric = IntelligenceFabric()
    observation = make_observation("obs-001")

    fabric.publish(observation)

    assert fabric.get("obs-001", tenant_id="tenant-a") == observation

    with pytest.raises(PermissionError):
        fabric.get("obs-001", tenant_id="tenant-b")


def test_duplicate_observation_ids_are_rejected() -> None:
    fabric = IntelligenceFabric()
    fabric.publish(make_observation("obs-001"))

    with pytest.raises(ValueError):
        fabric.publish(make_observation("obs-001"))


def test_query_filters_by_domain_kind_and_status() -> None:
    fabric = IntelligenceFabric()

    fabric.publish(
        make_observation(
            "obs-001",
            domain="business",
            kind="fact",
            status="verified",
        )
    )
    fabric.publish(
        make_observation(
            "obs-002",
            domain="marketing",
            kind="signal",
            status="observed",
        )
    )
    fabric.publish(
        make_observation(
            "obs-003",
            domain="business",
            kind="fact",
            status="observed",
        )
    )

    result = fabric.query(
        IntelligenceQuery(
            tenant_id="tenant-a",
            domains=("business",),
            kinds=("fact",),
            statuses=("verified",),
        )
    )

    assert [item.observation_id for item in result] == ["obs-001"]


def test_query_cannot_return_another_tenant() -> None:
    fabric = IntelligenceFabric()

    fabric.publish(make_observation("obs-a", tenant_id="tenant-a"))
    fabric.publish(make_observation("obs-b", tenant_id="tenant-b"))

    result = fabric.query(
        IntelligenceQuery(tenant_id="tenant-a")
    )

    assert [item.observation_id for item in result] == ["obs-a"]


def test_list_tenant_returns_only_that_tenants_intelligence() -> None:
    fabric = IntelligenceFabric()

    fabric.publish(make_observation("obs-a1", tenant_id="tenant-a"))
    fabric.publish(make_observation("obs-a2", tenant_id="tenant-a"))
    fabric.publish(make_observation("obs-b1", tenant_id="tenant-b"))

    result = fabric.list_tenant("tenant-a")

    assert {item.observation_id for item in result} == {"obs-a1", "obs-a2"}


def test_confidence_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValueError):
        make_observation("obs-invalid", confidence=1.1)

    with pytest.raises(ValueError):
        make_observation("obs-invalid-2", confidence=-0.1)


def test_required_identity_fields_are_validated() -> None:
    with pytest.raises(ValueError):
        make_observation("")

    with pytest.raises(ValueError):
        make_observation("obs-002", tenant_id="")


def test_related_and_dependency_references_are_supported() -> None:
    observation = IntelligenceObservation(
        observation_id="obs-relationship",
        tenant_id="tenant-a",
        domain="operations",
        kind="relationship",
        subject="vehicle.delivery",
        value={"relationship": "depends_on"},
        confidence=0.8,
        related_observation_ids=("obs-001",),
        dependency_observation_ids=("obs-002",),
    )

    assert observation.related_observation_ids == ("obs-001",)
    assert observation.dependency_observation_ids == ("obs-002",)
