from mananze_os.quote_readiness import assess_quote_readiness
from mananze_os.requirement_validation import (
    RequirementValidationFinding,
    RequirementValidationResult,
)


def make_validation(*dispositions):
    findings = tuple(
        RequirementValidationFinding(
            check_id=f"test:{index}",
            disposition=disposition,
            message=f"Test finding {index}",
        )
        for index, disposition in enumerate(dispositions)
    )

    return RequirementValidationResult(
        validation_id="validation:test",
        tenant_id="tenant:test",
        requirement_id="requirement:test",
        findings=findings,
    )


def test_valid_requirement_can_proceed():
    result = assess_quote_readiness(
        validation=make_validation("pass")
    )

    assert result.can_quote_automatically is True
    assert result.must_freeze is False
    assert result.decision.reason == "ready"


def test_review_finding_freezes_quote():
    result = assess_quote_readiness(
        validation=make_validation("pass", "review_required")
    )

    assert result.can_quote_automatically is False
    assert result.must_freeze is True
    assert result.decision.reason == "review_required"


def test_conflict_finding_freezes_quote():
    result = assess_quote_readiness(
        validation=make_validation("pass", "conflict")
    )

    assert result.must_freeze is True
    assert result.decision.reason == "conflict"


def test_insufficient_evidence_freezes_quote():
    result = assess_quote_readiness(
        validation=make_validation("insufficient_evidence")
    )

    assert result.must_freeze is True
    assert result.decision.reason == "insufficient_evidence"


def test_multiple_exceptions_prioritize_conflict():
    result = assess_quote_readiness(
        validation=make_validation(
            "review_required",
            "insufficient_evidence",
            "conflict",
        )
    )

    assert result.must_freeze is True
    assert result.decision.reason == "conflict"


def test_fulfilment_assessment_can_be_attached_without_mutation():
    result = assess_quote_readiness(
        validation=make_validation("pass"),
        fulfilment=None,
    )

    assert result.fulfilment is None
    assert result.can_quote_automatically is True
