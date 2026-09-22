from mananze_os.expense_discovery import (
    ExpenseDiscovery,
    ExpenseEvidence,
)
from mananze_os.payment_solution_intelligence import ExpenseRecord


def test_expense_discovery_groups_suppliers_and_tenants():
    discovery = ExpenseDiscovery()

    expenses = (
        ExpenseRecord(
            expense_id="EXP-001",
            tenant_id="tenant-a",
            supplier="SecureGuard",
            category="security",
            amount=5000,
            currency="ZAR",
            status="paid",
            recurring=True,
            frequency="monthly",
        ),
        ExpenseRecord(
            expense_id="EXP-002",
            tenant_id="tenant-a",
            supplier="SecureGuard",
            category="security",
            amount=5000,
            currency="ZAR",
            status="pending",
            recurring=True,
            frequency="monthly",
        ),
        ExpenseRecord(
            expense_id="EXP-003",
            tenant_id="tenant-b",
            supplier="Other Supplier",
            category="internet",
            amount=1000,
            currency="ZAR",
            status="paid",
        ),
    )

    evidence = (
        ExpenseEvidence(
            evidence_id="EVID-001",
            tenant_id="tenant-a",
            source_type="invoice",
            source_reference="invoice-001",
        ),
        ExpenseEvidence(
            evidence_id="EVID-002",
            tenant_id="tenant-b",
            source_type="invoice",
            source_reference="invoice-002",
        ),
    )

    result = discovery.discover(
        tenant_id="tenant-a",
        expenses=expenses,
        evidence=evidence,
    )

    assert len(result.expenses) == 2
    assert len(result.evidence) == 1
    assert len(result.suppliers) == 1

    supplier = result.suppliers[0]

    assert supplier.name == "SecureGuard"
    assert supplier.tenant_id == "tenant-a"
    assert supplier.recurring_expense_count == 2
    assert supplier.total_expense_value == 10000
    assert supplier.categories == ("security",)


def test_expense_discovery_requires_tenant_id():
    discovery = ExpenseDiscovery()

    try:
        discovery.discover(
            tenant_id="",
            expenses=(),
        )
        assert False, "expected tenant_id validation"
    except ValueError as exc:
        assert "tenant_id is required" in str(exc)


def test_expense_discovery_isolates_evidence_by_tenant():
    discovery = ExpenseDiscovery()

    expenses = (
        ExpenseRecord(
            expense_id="EXP-001",
            tenant_id="tenant-a",
            supplier="InternetCo",
            category="internet",
            amount=500,
            currency="ZAR",
            status="paid",
        ),
    )

    evidence = (
        ExpenseEvidence(
            evidence_id="EVID-A",
            tenant_id="tenant-a",
            source_type="invoice",
            source_reference="invoice-a",
        ),
        ExpenseEvidence(
            evidence_id="EVID-B",
            tenant_id="tenant-b",
            source_type="invoice",
            source_reference="invoice-b",
        ),
    )

    result = discovery.discover(
        tenant_id="tenant-a",
        expenses=expenses,
        evidence=evidence,
    )

    assert [item.evidence_id for item in result.evidence] == ["EVID-A"]
