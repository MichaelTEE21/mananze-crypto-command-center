from mananze_os.obligation_intelligence import (
    Obligation,
    ObligationDependency,
)


def test_obligation_accepts_valid_data():
    obligation = Obligation(
        obligation_id="OBL-001",
        tenant_id="tenant-a",
        name="Monthly Security Service",
        obligation_type="security" if False else "service",
        counterparty="SecureGuard",
        amount=5000,
        currency="ZAR",
        frequency="monthly",
        due_date="2026-10-01",
        status="active",
        approval_required=True,
        source_reference="invoice-001",
    )

    assert obligation.obligation_id == "OBL-001"
    assert obligation.tenant_id == "tenant-a"
    assert obligation.counterparty == "SecureGuard"
    assert obligation.amount == 5000
    assert obligation.frequency == "monthly"
    assert obligation.status == "active"


def test_obligation_supports_non_financial_commitments():
    obligation = Obligation(
        obligation_id="OBL-002",
        tenant_id="tenant-a",
        name="Annual Operating Licence",
        obligation_type="licence",
        counterparty="Regulatory Authority",
        renewal_date="2027-03-31",
        status="active",
    )

    assert obligation.obligation_type == "licence"
    assert obligation.amount is None
    assert obligation.renewal_date == "2027-03-31"


def test_obligation_dependency_accepts_valid_data():
    dependency = ObligationDependency(
        dependency_id="DEP-001",
        tenant_id="tenant-a",
        obligation_id="OBL-001",
        depends_on="premises security",
        impact="Business operations depend on continuous security coverage",
    )

    assert dependency.dependency_id == "DEP-001"
    assert dependency.tenant_id == "tenant-a"
    assert dependency.obligation_id == "OBL-001"


def test_obligation_rejects_empty_identity():
    try:
        Obligation(
            obligation_id="",
            tenant_id="tenant-a",
            name="Internet",
            obligation_type="service",
            counterparty="InternetCo",
        )
        assert False, "expected obligation_id validation"
    except ValueError as exc:
        assert "obligation_id is required" in str(exc)


def test_obligation_requires_currency_for_amount():
    try:
        Obligation(
            obligation_id="OBL-003",
            tenant_id="tenant-a",
            name="Internet",
            obligation_type="service",
            counterparty="InternetCo",
            amount=500,
        )
        assert False, "expected currency validation"
    except ValueError as exc:
        assert "currency is required" in str(exc)


def test_obligation_rejects_negative_amount():
    try:
        Obligation(
            obligation_id="OBL-004",
            tenant_id="tenant-a",
            name="Internet",
            obligation_type="service",
            counterparty="InternetCo",
            amount=-1,
            currency="ZAR",
        )
        assert False, "expected negative amount validation"
    except ValueError as exc:
        assert "amount cannot be negative" in str(exc)
