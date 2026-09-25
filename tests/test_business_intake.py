from datetime import datetime, timezone

import pytest

from mananze_os.business_intake import (
    BusinessIntakeCase,
    IntakeEvidence,
)


def test_new_intake_starts_created():
    intake = BusinessIntakeCase(
        intake_id="intake:001",
        tenant_id="tenant:security-001",
    )

    assert intake.status == "created"
    assert intake.evidence == []


def test_evidence_moves_created_intake_to_collecting():
    intake = BusinessIntakeCase(
        intake_id="intake:001",
        tenant_id="tenant:security-001",
    )

    evidence = IntakeEvidence(
        evidence_id="evidence:001",
        tenant_id="tenant:security-001",
        source_type="pdf",
        source_reference="services.pdf",
    )

    intake.add_evidence(evidence)

    assert intake.status == "collecting"
    assert intake.evidence_references()[0].evidence_id == "evidence:001"


def test_cross_tenant_evidence_is_rejected():
    intake = BusinessIntakeCase(
        intake_id="intake:001",
        tenant_id="tenant:security-001",
    )

    evidence = IntakeEvidence(
        evidence_id="evidence:001",
        tenant_id="tenant:other",
        source_type="pdf",
        source_reference="services.pdf",
    )

    with pytest.raises(PermissionError):
        intake.add_evidence(evidence)


def test_duplicate_evidence_is_rejected():
    intake = BusinessIntakeCase(
        intake_id="intake:001",
        tenant_id="tenant:security-001",
    )

    evidence = IntakeEvidence(
        evidence_id="evidence:001",
        tenant_id="tenant:security-001",
        source_type="pdf",
        source_reference="services.pdf",
    )

    intake.add_evidence(evidence)

    with pytest.raises(ValueError, match="evidence_id already exists"):
        intake.add_evidence(evidence)


def test_analysis_cannot_start_without_evidence():
    intake = BusinessIntakeCase(
        intake_id="intake:001",
        tenant_id="tenant:security-001",
    )

    with pytest.raises(ValueError, match="without evidence"):
        intake.transition("ready_for_analysis")


def test_intake_can_progress_to_analysis():
    intake = BusinessIntakeCase(
        intake_id="intake:001",
        tenant_id="tenant:security-001",
    )

    intake.add_evidence(
        IntakeEvidence(
            evidence_id="evidence:001",
            tenant_id="tenant:security-001",
            source_type="website",
            source_reference="https://example.test",
        )
    )

    intake.transition("ready_for_analysis")
    assert intake.status == "ready_for_analysis"

    intake.transition("analysing")
    assert intake.status == "analysing"

    intake.transition("analysis_complete")
    assert intake.status == "analysis_complete"

    intake.transition("twin_build_ready")
    assert intake.status == "twin_build_ready"


def test_twin_build_requires_completed_analysis():
    intake = BusinessIntakeCase(
        intake_id="intake:001",
        tenant_id="tenant:security-001",
    )

    intake.add_evidence(
        IntakeEvidence(
            evidence_id="evidence:001",
            tenant_id="tenant:security-001",
            source_type="pdf",
            source_reference="company-profile.pdf",
        )
    )

    intake.transition("ready_for_analysis")
    intake.transition("analysing")

    with pytest.raises(ValueError, match="analysis is complete"):
        intake.transition("twin_build_ready")


def test_timestamps_are_timezone_aware():
    intake = BusinessIntakeCase(
        intake_id="intake:001",
        tenant_id="tenant:security-001",
    )

    assert intake.created_at.tzinfo == timezone.utc
    assert intake.updated_at.tzinfo == timezone.utc


def test_invalid_blank_identity_is_rejected():
    with pytest.raises(ValueError, match="intake_id is required"):
        BusinessIntakeCase(
            intake_id=" ",
            tenant_id="tenant:security-001",
        )

    with pytest.raises(ValueError, match="tenant_id is required"):
        BusinessIntakeCase(
            intake_id="intake:001",
            tenant_id=" ",
        )
