from mananze_os.evidence_analysis import (
    EvidenceAnalysisEngine,
    EvidenceAnalysisRequest,
    EvidenceObservationProposal,
    StaticEvidenceAnalysisProvider,
)
from mananze_os.evidence_reference import EvidenceReference


def make_evidence(
    *,
    tenant_id="tenant-001",
    evidence_id="evidence-001",
):
    return EvidenceReference(
        evidence_id=evidence_id,
        tenant_id=tenant_id,
        source_type="document",
        source_reference="rate-card.pdf",
        quality="strong",
        description="Guarding rate card",
    )


def make_request(
    *,
    tenant_id="tenant-001",
):
    evidence = make_evidence(tenant_id=tenant_id)

    return EvidenceAnalysisRequest(
        tenant_id=tenant_id,
        evidence=evidence,
        content={"hourly_rate": 25},
    )


def test_analysis_produces_intelligence_observation():
    provider = StaticEvidenceAnalysisProvider(
        (
            EvidenceObservationProposal(
                domain="pricing",
                kind="fact",
                subject="hourly_guard_rate",
                value=25,
                confidence=0.94,
            ),
        )
    )

    result = EvidenceAnalysisEngine(provider).analyze(make_request())

    assert len(result) == 1

    observation = result[0]

    assert observation.tenant_id == "tenant-001"
    assert observation.domain == "pricing"
    assert observation.kind == "fact"
    assert observation.subject == "hourly_guard_rate"
    assert observation.value == 25
    assert observation.confidence == 0.94
    assert observation.status == "observed"
    assert observation.source_reference == "rate-card.pdf"


def test_analysis_preserves_evidence_provenance():
    provider = StaticEvidenceAnalysisProvider(
        (
            EvidenceObservationProposal(
                domain="operations",
                kind="fact",
                subject="service_area",
                value="Gauteng",
                confidence=0.9,
            ),
        )
    )

    evidence = EvidenceReference(
        evidence_id="evidence-002",
        tenant_id="tenant-001",
        source_type="website",
        source_reference="https://example.co.za",
        quality="moderate",
    )

    request = EvidenceAnalysisRequest(
        tenant_id="tenant-001",
        evidence=evidence,
        content="Service area: Gauteng",
    )

    result = EvidenceAnalysisEngine(provider).analyze(request)

    assert result[0].source_reference == "https://example.co.za"


def test_cross_tenant_evidence_is_rejected():
    evidence = make_evidence(tenant_id="tenant-002")

    provider = StaticEvidenceAnalysisProvider(())

    try:
        EvidenceAnalysisRequest(
            tenant_id="tenant-001",
            evidence=evidence,
            content="secret",
        )
    except PermissionError as exc:
        assert "tenant" in str(exc).lower()
    else:
        raise AssertionError("expected cross-tenant analysis rejection")


def test_analysis_cannot_mark_observation_verified():
    provider = StaticEvidenceAnalysisProvider(
        (
            EvidenceObservationProposal(
                domain="identity",
                kind="fact",
                subject="legal_name",
                value="Example Security",
                confidence=0.99,
                status="verified",
            ),
        )
    )

    try:
        EvidenceAnalysisEngine(provider).analyze(make_request())
    except PermissionError as exc:
        assert "verified" in str(exc).lower()
    else:
        raise AssertionError("expected verification rejection")


def test_observation_ids_are_deterministic():
    provider = StaticEvidenceAnalysisProvider(
        (
            EvidenceObservationProposal(
                domain="pricing",
                kind="fact",
                subject="hourly_guard_rate",
                value=25,
                confidence=0.94,
            ),
        )
    )

    engine = EvidenceAnalysisEngine(provider)

    first = engine.analyze(make_request())[0]
    second = engine.analyze(make_request())[0]

    assert first.observation_id == second.observation_id


def test_different_evidence_produces_different_observation_id():
    provider = StaticEvidenceAnalysisProvider(
        (
            EvidenceObservationProposal(
                domain="pricing",
                kind="fact",
                subject="hourly_guard_rate",
                value=25,
                confidence=0.94,
            ),
        )
    )

    engine = EvidenceAnalysisEngine(provider)

    first = engine.analyze(
        EvidenceAnalysisRequest(
            tenant_id="tenant-001",
            evidence=make_evidence(evidence_id="evidence-001"),
            content={"hourly_rate": 25},
        )
    )[0]

    second = engine.analyze(
        EvidenceAnalysisRequest(
            tenant_id="tenant-001",
            evidence=make_evidence(evidence_id="evidence-999"),
            content={"hourly_rate": 25},
        )
    )[0]

    assert first.observation_id != second.observation_id


def test_inferred_observation_is_allowed_but_not_verified():
    provider = StaticEvidenceAnalysisProvider(
        (
            EvidenceObservationProposal(
                domain="operations",
                kind="signal",
                subject="likely_24_hour_service",
                value=True,
                confidence=0.61,
                status="inferred",
            ),
        )
    )

    result = EvidenceAnalysisEngine(provider).analyze(make_request())

    assert result[0].status == "inferred"


def test_invalid_confidence_is_rejected():
    try:
        EvidenceObservationProposal(
            domain="pricing",
            kind="fact",
            subject="hourly_rate",
            value=25,
            confidence=1.1,
        )
    except ValueError as exc:
        assert "confidence" in str(exc)
    else:
        raise AssertionError("expected confidence validation error")


def test_multiple_observations_from_one_evidence_are_supported():
    provider = StaticEvidenceAnalysisProvider(
        (
            EvidenceObservationProposal(
                domain="operations",
                kind="fact",
                subject="service_area",
                value="Gauteng",
                confidence=0.95,
            ),
            EvidenceObservationProposal(
                domain="pricing",
                kind="fact",
                subject="hourly_guard_rate",
                value=25,
                confidence=0.94,
            ),
        )
    )

    result = EvidenceAnalysisEngine(provider).analyze(make_request())

    assert len(result) == 2
    assert {item.subject for item in result} == {
        "service_area",
        "hourly_guard_rate",
    }
