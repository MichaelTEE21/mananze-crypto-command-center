import pytest

from mananze_os.requirement import Requirement
from mananze_os.requirement_validation import (
    RequirementValidationFinding,
    RequirementValidationResult,
    RequirementValidator,
)


def make_requirement(**overrides):
    values = {
        "requirement_id": "req-001",
        "tenant_id": "tenant-001",
        "product_or_material": "18mm white melamine",
        "dimensions": "600x400",
        "quantity": 2,
        "specification": "standard",
        "evidence_ids": ("evidence-001",),
        "confirmation_status": "confirmed",
    }
    values.update(overrides)
    return Requirement(**values)


def test_validation_finding_accepts_valid_disposition():
    finding = RequirementValidationFinding(
        check_id="dimensions",
        disposition="pass",
        message="dimensions are present",
    )

    assert finding.disposition == "pass"


def test_validation_finding_rejects_invalid_disposition():
    with pytest.raises(
        ValueError,
        match="invalid requirement validation disposition",
    ):
        RequirementValidationFinding(
            check_id="dimensions",
            disposition="unknown",
            message="invalid",
        )


def test_validation_result_requires_review_for_review_finding():
    result = RequirementValidationResult(
        validation_id="validation-001",
        tenant_id="tenant-001",
        requirement_id="req-001",
        findings=(
            RequirementValidationFinding(
                check_id="dimensions",
                disposition="review_required",
                message="dimensions are missing",
            ),
        ),
    )

    assert result.requires_review is True
    assert result.passed is False


def test_confirmed_requirement_with_complete_core_fields_passes():
    result = RequirementValidator().validate(
        "validation-001",
        make_requirement(),
    )

    assert result.tenant_id == "tenant-001"
    assert result.requirement_id == "req-001"
    assert result.passed is True
    assert result.requires_review is False


def test_unconfirmed_requirement_requires_review():
    result = RequirementValidator().validate(
        "validation-001",
        make_requirement(confirmation_status="unconfirmed"),
    )

    assert result.requires_review is True


def test_partially_confirmed_requirement_requires_review():
    result = RequirementValidator().validate(
        "validation-001",
        make_requirement(confirmation_status="partially_confirmed"),
    )

    assert result.requires_review is True


def test_missing_evidence_requires_review():
    result = RequirementValidator().validate(
        "validation-001",
        make_requirement(evidence_ids=()),
    )

    assert result.requires_review is True


def test_missing_dimensions_requires_review():
    result = RequirementValidator().validate(
        "validation-001",
        make_requirement(dimensions=""),
    )

    assert result.requires_review is True


def test_blank_validation_id_is_rejected():
    with pytest.raises(ValueError, match="validation ID is required"):
        RequirementValidator().validate("", make_requirement())
