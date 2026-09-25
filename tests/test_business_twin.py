from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.business_twin import (
    BusinessTwinBuilder,
    BusinessTwinRegistry,
)
from mananze_os.business_truth import BusinessTruth


TENANT_ID = "tenant-001"


def truth(
    truth_id: str,
    subject: str,
    value,
    status: str = "established",
    tenant_id: str = TENANT_ID,
):
    now = datetime.now(timezone.utc)

    return BusinessTruth(
        truth_id=truth_id,
        tenant_id=tenant_id,
        subject=subject,
        value=value,
        status=status,
        confidence=0.9,
        source_type="business_document",
        source_reference=f"doc-{truth_id}",
        observation_ids=(f"obs-{truth_id}",),
        effective_at=now,
        resolved_at=now,
        conflict_observation_ids=(),
    )


def test_twin_requires_business_truth():
    with pytest.raises(ValueError):
        BusinessTwinBuilder().build(
            tenant_id=TENANT_ID,
            truths=[],
        )


def test_twin_is_built_from_truth():
    twin = BusinessTwinBuilder().build(
        tenant_id=TENANT_ID,
        truths=[
            truth("t1", "services", {"name": "Guarding"}),
            truth("t2", "locations", {"city": "Benoni"}),
            truth("t3", "systems", {"name": "WhatsApp"}),
        ],
    )

    assert twin.tenant_id == TENANT_ID
    assert twin.status == "active"
    assert len(twin.services) == 1
    assert len(twin.locations) == 1
    assert len(twin.systems) == 1
    assert twin.truth_ids == ("t1", "t2", "t3")


def test_conflicting_truth_is_preserved():
    twin = BusinessTwinBuilder().build(
        tenant_id=TENANT_ID,
        truths=[
            truth(
                "t1",
                "pricing",
                {"monthly": 10000},
                status="conflicting",
            ),
            truth(
                "t2",
                "services",
                {"name": "Guarding"},
            ),
        ],
    )

    assert twin.status == "conflicted"
    assert len(twin.conflicts) == 1
    assert twin.conflicts[0]["value"] == {"monthly": 10000}


def test_unknown_truth_becomes_gap():
    twin = BusinessTwinBuilder().build(
        tenant_id=TENANT_ID,
        truths=[
            truth("t1", "unknown_operating_rule", {"value": "x"}),
        ],
    )

    assert twin.status == "incomplete"
    assert len(twin.gaps) == 1


def test_stale_truth_marks_twin_stale():
    twin = BusinessTwinBuilder().build(
        tenant_id=TENANT_ID,
        truths=[
            truth("t1", "pricing", {"monthly": 10000}, status="stale"),
        ],
    )

    assert twin.status == "stale"


def test_cross_tenant_truth_is_rejected():
    with pytest.raises(PermissionError):
        BusinessTwinBuilder().build(
            tenant_id=TENANT_ID,
            truths=[
                truth(
                    "t1",
                    "services",
                    {"name": "Guarding"},
                    tenant_id="tenant-002",
                )
            ],
        )


def test_twin_id_is_deterministic():
    truths = [
        truth("t1", "services", {"name": "Guarding"}),
        truth("t2", "locations", {"city": "Benoni"}),
    ]

    first = BusinessTwinBuilder().build(
        tenant_id=TENANT_ID,
        truths=truths,
    )

    second = BusinessTwinBuilder().build(
        tenant_id=TENANT_ID,
        truths=truths,
    )

    assert first.twin_id == second.twin_id


def test_registry_is_tenant_isolated():
    builder = BusinessTwinBuilder()
    registry = BusinessTwinRegistry()

    twin = builder.build(
        tenant_id=TENANT_ID,
        truths=[
            truth("t1", "services", {"name": "Guarding"}),
        ],
    )

    registry.put(twin)

    assert registry.get(twin.twin_id, TENANT_ID) == twin

    with pytest.raises(KeyError):
        registry.get(twin.twin_id, "tenant-002")


def test_registry_lists_only_requested_tenant():
    builder = BusinessTwinBuilder()
    registry = BusinessTwinRegistry()

    first = builder.build(
        tenant_id="tenant-001",
        truths=[truth("t1", "services", {"name": "A"})],
    )

    second = builder.build(
        tenant_id="tenant-002",
        truths=[
            truth(
                "t2",
                "services",
                {"name": "B"},
                tenant_id="tenant-002",
            )
        ],
    )

    registry.put(first)
    registry.put(second)

    result = registry.list_tenant("tenant-001")

    assert result == [first]


def test_twin_preserves_provenance():
    twin = BusinessTwinBuilder().build(
        tenant_id=TENANT_ID,
        truths=[
            truth("t1", "services", {"name": "Guarding"}),
        ],
    )

    record = twin.services[0]

    assert record["source_type"] == "business_document"
    assert record["source_reference"] == "doc-t1"
    assert record["observation_ids"] == ["obs-t1"]
