from mananze_os.payment_solution_intelligence import ExpenseRecord
from mananze_os.recurring_expense_intelligence import (
    RecurringExpenseIntelligence,
)


def make_expense(
    expense_id: str,
    amount: float,
    recurring: bool = True,
    frequency: str | None = "monthly",
) -> ExpenseRecord:
    return ExpenseRecord(
        expense_id=expense_id,
        tenant_id="tenant-a",
        supplier="SecureGuard",
        category="security",
        amount=amount,
        currency="ZAR",
        status="paid",
        recurring=recurring,
        frequency=frequency,
    )


def test_detects_single_recurring_expense():
    intelligence = RecurringExpenseIntelligence()

    patterns = intelligence.detect(
        "tenant-a",
        (make_expense("EXP-001", 18000),),
    )

    assert len(patterns) == 1
    assert patterns[0].supplier == "SecureGuard"
    assert patterns[0].category == "security"
    assert patterns[0].occurrence_count == 1
    assert patterns[0].status == "detected"


def test_two_occurrences_strengthen_pattern():
    intelligence = RecurringExpenseIntelligence()

    patterns = intelligence.detect(
        "tenant-a",
        (
            make_expense("EXP-001", 18000),
            make_expense("EXP-002", 18000),
        ),
    )

    assert len(patterns) == 1
    assert patterns[0].occurrence_count == 2
    assert patterns[0].status == "detected"
    assert patterns[0].confidence == 0.55


def test_three_occurrences_become_likely():
    intelligence = RecurringExpenseIntelligence()

    patterns = intelligence.detect(
        "tenant-a",
        (
            make_expense("EXP-001", 18000),
            make_expense("EXP-002", 18000),
            make_expense("EXP-003", 18400),
        ),
    )

    assert len(patterns) == 1
    assert patterns[0].occurrence_count == 3
    assert patterns[0].typical_amount == 18133.333333333332
    assert patterns[0].status == "likely"
    assert patterns[0].confidence == 0.65


def test_non_recurring_expenses_are_not_detected():
    intelligence = RecurringExpenseIntelligence()

    patterns = intelligence.detect(
        "tenant-a",
        (
            make_expense(
                "EXP-001",
                18000,
                recurring=False,
                frequency=None,
            ),
        ),
    )

    assert patterns == ()


def test_tenant_isolation():
    intelligence = RecurringExpenseIntelligence()

    other_tenant_expense = ExpenseRecord(
        expense_id="EXP-B",
        tenant_id="tenant-b",
        supplier="SecureGuard",
        category="security",
        amount=18000,
        currency="ZAR",
        status="paid",
        recurring=True,
        frequency="monthly",
    )

    patterns = intelligence.detect(
        "tenant-a",
        (other_tenant_expense,),
    )

    assert patterns == ()


def test_builds_obligation_candidate_from_pattern():
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

    assert len(candidates) == 1
    assert candidates[0].tenant_id == "tenant-a"
    assert candidates[0].counterparty == "SecureGuard"
    assert candidates[0].obligation_type == "expense"
    assert candidates[0].frequency == "monthly"
    assert candidates[0].status == "likely"
    assert candidates[0].evidence_expense_ids == (
        "EXP-001",
        "EXP-002",
        "EXP-003",
    )


def test_empty_tenant_is_rejected():
    intelligence = RecurringExpenseIntelligence()

    try:
        intelligence.detect("", ())
        assert False, "expected tenant validation"
    except ValueError as exc:
        assert "tenant_id is required" in str(exc)
