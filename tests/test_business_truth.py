
from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.business_truth import (
    BusinessTruthResolver,
    TruthCandidate,
)
from mananze_os.intelligence_fabric import IntelligenceObservation


TENANT_ID = "tenant-001"


def observation(
    observation_id: str,
    subject: str,
    value: object,
    *,
    confidence: float = 0.9,
    status: str = "observed",
    source_reference: str = "evidence-001",
    tenant_id: str = TENANT_ID,
) -> IntelligenceObservation:
    return IntelligenceObservation(
        observation_id=observation_id,
        tenant_id=tenant_id,
        domain="business",
        kind="fact",
        subject=subject,
        value=value,
        status=status,
        confidence=confidence,
        source_reference=source_reference,
    )


def test_resolves_agreeing_evidence_into_established_truth():
    resolver = BusinessTruthResolver()

    result = resolver.resolve(
        (
            TruthCandidate(
                observation("obs-1", "business.name", "ABC Security"),
                source_type="business_document",
                source_quality=0.9,
            ),
            TruthCandidate(
                observation("obs-2", "business.name", "ABC Security"),
                source_type="website",
                source_quality=0.8,
            ),
        ),
        tenant_id=TENANT_ID,
    )

    assert len(result) == 1
    assert result[0].status == "established"
    assert result[0].value == "ABC Security"
    assert result[0].source_type == "business_document"
    assert result[0].observation_ids == ("obs-1", "obs-2")


def test_source_precedence_is_used_when_evidence_agrees():
    resolver = BusinessTruthResolver()

    result = resolver.resolve(
        (
            TruthCandidate(
                observation("obs-1", "business.name", "ABC"),
                source_type="website",
                source_quality=1.0,
            ),
            TruthCandidate(
                observation("obs-2", "business.name", "ABC"),
                source_type="human_confirmed",
                source_quality=0.7,
            ),
        ),
        tenant_id=TENANT_ID,
    )

    assert result[0].source_type == "human_confirmed"


def test_conflicting_values_are_not_silently_resolved():
    resolver = BusinessTruthResolver()

    result = resolver.resolve(
        (
            TruthCandidate(
                observation("obs-1", "business.rate", 12000),
                source_type="business_document",
                source_quality=1.0,
            ),
            TruthCandidate(
                observation("obs-2", "business.rate", 15000),
                source_type="website",
                source_quality=1.0,
            ),
        ),
        tenant_id=TENANT_ID,
    )

    truth = result[0]

    assert truth.status == "conflicting"
    assert truth.conflict_observation_ids == ("obs-1", "obs-2")
    assert truth.value["conflict"] is True
    assert len(truth.value["candidates"]) == 2


def test_inferred_observation_remains_inferred_truth():
    resolver = BusinessTruthResolver()

    result = resolver.resolve(
        (
            TruthCandidate(
                observation(
                    "obs-1",
                    "service.category",
                    "security",
                    status="inferred",
                ),
                source_type="inference",
                source_quality=0.5,
            ),
        ),
        tenant_id=TENANT_ID,
    )

    assert result[0].status == "inferred"


def test_expired_observation_becomes_stale():
    resolver = BusinessTruthResolver()

    expired = observation(
        "obs-1",
        "rate",
        12000,
    )

    expired = IntelligenceObservation(
        observation_id=expired.observation_id,
        tenant_id=expired.tenant_id,
        domain=expired.domain,
        kind=expired.kind,
        subject=expired.subject,
        value=expired.value,
        status=expired.status,
        confidence=expired.confidence,
        source_reference=expired.source_reference,
        observed_at=expired.observed_at,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )

    result = resolver.resolve(
        (
            TruthCandidate(
                observation=expired,
                source_type="business_document",
                source_quality=1.0,
            ),
        ),
        tenant_id=TENANT_ID,
    )

    assert result[0].status == "stale"


def test_cross_tenant_resolution_is_rejected():
    resolver = BusinessTruthResolver()

    foreign = IntelligenceObservation(
        observation_id="foreign-1",
        tenant_id="tenant-999",
        domain="business",
        kind="fact",
        subject="business.name",
        value="Other Business",
        confidence=0.9,
    )

    with pytest.raises(PermissionError):
        resolver.resolve(
            (
                TruthCandidate(
                    observation=foreign,
                    source_type="business_document",
                    source_quality=1.0,
                ),
            ),
            tenant_id=TENANT_ID,
        )


def test_cross_tenant_truth_access_is_rejected():
    resolver = BusinessTruthResolver()

    result = resolver.resolve(
        (
            TruthCandidate(
                observation("obs-1", "business.name", "ABC"),
                source_type="business_document",
                source_quality=1.0,
            ),
        ),
        tenant_id=TENANT_ID,
    )

    with pytest.raises(PermissionError):
        resolver.get(
            result[0].truth_id,
            tenant_id="tenant-999",
        )


def test_truth_ids_are_deterministic():
    resolver = BusinessTruthResolver()

    first = resolver.resolve(
        (
            TruthCandidate(
                observation("obs-1", "business.name", "ABC"),
                source_type="business_document",
                source_quality=1.0,
            ),
        ),
        tenant_id=TENANT_ID,
    )[0]

    second_resolver = BusinessTruthResolver()

    second = second_resolver.resolve(
        (
            TruthCandidate(
                observation("obs-2", "business.name", "ABC"),
                source_type="website",
                source_quality=0.8,
            ),
        ),
        tenant_id=TENANT_ID,
    )[0]

    assert first.truth_id == second.truth_id


def test_multiple_subjects_produce_separate_truth_records():
    resolver = BusinessTruthResolver()

    result = resolver.resolve(
        (
            TruthCandidate(
                observation("obs-1", "business.name", "ABC"),
                source_type="business_document",
                source_quality=1.0,
            ),
            TruthCandidate(
                observation("obs-2", "business.city", "Benoni"),
                source_type="business_document",
                source_quality=1.0,
            ),
        ),
        tenant_id=TENANT_ID,
    )

    assert len(result) == 2
    assert {
        truth.subject
        for truth in result
    } == {"business.name", "business.city"}


def test_truth_can_be_listed_by_tenant():
    resolver = BusinessTruthResolver()

    resolver.resolve(
        (
            TruthCandidate(
                observation("obs-1", "business.name", "ABC"),
                source_type="business_document",
                source_quality=1.0,
            ),
        ),
        tenant_id=TENANT_ID,
    )

    resolver.resolve(
        (
            TruthCandidate(
                observation(
                    "obs-2",
                    "business.name",
                    "XYZ",
                    tenant_id="tenant-002",
                ),
                source_type="business_document",
                source_quality=1.0,
            ),
        ),
        tenant_id="tenant-002",
    )

    assert len(resolver.list_tenant(TENANT_ID)) == 1
    assert resolver.list_tenant(TENANT_ID)[0].value == "ABC"
