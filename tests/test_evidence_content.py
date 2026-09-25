from mananze_os.evidence_content import (
    EvidenceContentIngestion,
    EvidenceExtractionRequest,
    PassthroughEvidenceExtractor,
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
    content_type="text/plain",
    raw_content="Hourly guard rate: R25",
):
    return EvidenceExtractionRequest(
        tenant_id=tenant_id,
        evidence=make_evidence(tenant_id=tenant_id),
        raw_content=raw_content,
        content_type=content_type,
    )


def test_ingestion_returns_analysis_ready_content():
    extractor = PassthroughEvidenceExtractor()

    result = EvidenceContentIngestion(extractor).ingest(
        make_request()
    )

    assert result.evidence_id == "evidence-001"
    assert result.tenant_id == "tenant-001"
    assert result.content_type == "text/plain"
    assert result.content == "Hourly guard rate: R25"
    assert result.extractor_id == "passthrough"


def test_content_hash_is_sha256():
    extractor = PassthroughEvidenceExtractor()

    result = EvidenceContentIngestion(extractor).ingest(
        make_request()
    )

    assert len(result.content_hash) == 64
    assert all(
        character in "0123456789abcdef"
        for character in result.content_hash
    )


def test_same_content_produces_same_hash():
    extractor = PassthroughEvidenceExtractor()
    ingestion = EvidenceContentIngestion(extractor)

    first = ingestion.ingest(make_request())
    second = ingestion.ingest(make_request())

    assert first.content_hash == second.content_hash


def test_different_content_produces_different_hash():
    extractor = PassthroughEvidenceExtractor()
    ingestion = EvidenceContentIngestion(extractor)

    first = ingestion.ingest(
        make_request(raw_content="Hourly guard rate: R25")
    )

    second = ingestion.ingest(
        make_request(raw_content="Hourly guard rate: R30")
    )

    assert first.content_hash != second.content_hash


def test_cross_tenant_evidence_is_rejected():
    evidence = make_evidence(tenant_id="tenant-002")

    try:
        EvidenceExtractionRequest(
            tenant_id="tenant-001",
            evidence=evidence,
            raw_content="secret",
            content_type="text/plain",
        )
    except PermissionError as exc:
        assert "tenant" in str(exc).lower()
    else:
        raise AssertionError("expected cross-tenant rejection")


def test_unsupported_content_type_is_rejected():
    extractor = PassthroughEvidenceExtractor()

    try:
        EvidenceContentIngestion(extractor).ingest(
            make_request(content_type="application/pdf")
        )
    except ValueError as exc:
        assert "content type" in str(exc).lower()
    else:
        raise AssertionError("expected unsupported content type rejection")


def test_json_content_is_supported():
    extractor = PassthroughEvidenceExtractor()

    result = EvidenceContentIngestion(extractor).ingest(
        make_request(
            content_type="application/json",
            raw_content={"hourly_rate": 25},
        )
    )

    assert result.content == {"hourly_rate": 25}


def test_html_content_is_supported():
    extractor = PassthroughEvidenceExtractor()

    result = EvidenceContentIngestion(extractor).ingest(
        make_request(
            content_type="text/html",
            raw_content="<html><body>Security Services</body></html>",
        )
    )

    assert "Security Services" in result.content


def test_extractor_identity_is_preserved():
    extractor = PassthroughEvidenceExtractor(
        extractor_id="controlled-test-extractor"
    )

    result = EvidenceContentIngestion(extractor).ingest(
        make_request()
    )

    assert result.extractor_id == "controlled-test-extractor"


def test_blank_extractor_identity_is_rejected():
    try:
        PassthroughEvidenceExtractor(extractor_id=" ")
    except ValueError as exc:
        assert "extractor" in str(exc).lower()
    else:
        raise AssertionError("expected extractor identity validation")


def test_blank_content_type_is_rejected():
    try:
        EvidenceExtractionRequest(
            tenant_id="tenant-001",
            evidence=make_evidence(),
            raw_content="test",
            content_type=" ",
        )
    except ValueError as exc:
        assert "content_type" in str(exc)
    else:
        raise AssertionError("expected content type validation")
