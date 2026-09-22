from mananze_os.evidence_reference import (
    EvidenceReference,
    ObligationCandidateValidator,
)
from mananze_os.payment_solution_intelligence import ExpenseRecord
from mananze_os.recurring_expense_intelligence import (
    RecurringExpenseIntelligence,
)


def make_expense(expense_id: str, amount: float) -> ExpenseRecord:
    return ExpenseRecord(
        expense_id=expense_id,
        tenant_id="tenant-a",
        supplier="SecureGuard",
        category="security",
        amount=amount,
        currency="ZAR",
        status="paid",
        recurring=True,
        frequency="monthly",
    )


def make_candidate():
    intelligence = RecurringExpenseIntelligence()

    patterns = intelligence.detect(
        "tenant-a",
        (
            make_expense("EXP-001", 18000),
            make_expense("EXP-002", 18000),
            make_expense("EXP-003", 18400),
        ),
    )

    candidates = intelligence.build_candidates(patterns)

    return candidates[0]


def make_evidence(
    evidence_id: str,
    tenant_id: str = "tenant-a",
    quality: str = "strong",
) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=evidence_id,
        tenant_id=tenant_id,
        source_type="expense_record",
        source_reference=evidence_id,
        quality=quality,
        description="Client-provided expense evidence",
    )


def test_supported_candidate_is_validated():
    candidate = make_candidate()

    evidence = (
        make_evidence("EXP-001"),
        make_evidence("EXP-002"),
        make_evidence("EXP-003"),
    )

    result = ObligationCandidateValidator().validate(
        candidate,
        evidence,
    )

    assert result.status == "supported"
    assert result.evidence_count == 3
    assert result.evidence_ids == (
        "EXP-001",
        "EXP-002",
        "EXP-003",
    )


def test_missing_evidence_is_insufficient():
    candidate = make_candidate()

    result = ObligationCandidateValidator().validate(
        candidate,
        (),
    )

    assert result.status == "insufficient_evidence"
    assert result.evidence_count == 0


def test_other_tenant_evidence_is_not_used():
    candidate = make_candidate()

    evidence = (
        make_evidence("EXP-001", tenant_id="tenant-b"),
        make_evidence("EXP-002", tenant_id="tenant-b"),
        make_evidence("EXP-003", tenant_id="tenant-b"),
    )

    result = ObligationCandidateValidator().validate(
        candidate,
        evidence,
    )

    assert result.status == "insufficient_evidence"
    assert result.evidence_count == 0


def test_unresolved_evidence_is_conflicting():
    candidate = make_candidate()

    evidence = (
        make_evidence("EXP-001", quality="unknown"),
        make_evidence("EXP-002", quality="strong"),
    )

    result = ObligationCandidateValidator().validate(
        candidate,
        evidence,
    )

    assert result.status == "conflicting_evidence"


def test_candidate_validation_preserves_tenant():
    candidate = make_candidate()

    result = ObligationCandidateValidator().validate(
        candidate,
        (make_evidence("EXP-001"),),
    )

    assert result.tenant_id == "tenant-a"
    assert result.candidate_name == candidate.name


def test_empty_evidence_id_is_rejected():
    try:
        make_evidence("")
        assert False, "expected evidence validation"
    except ValueError as exc:
        assert "evidence_id is required" in str(exc)
