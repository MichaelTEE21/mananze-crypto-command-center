from mananze_os.expense_registry import ExpenseRegistry
from mananze_os.payment_solution_intelligence import ExpenseRecord


def test_expense_registry_registers_and_retrieves_expense():
    registry = ExpenseRegistry()

    expense = ExpenseRecord(
        expense_id="EXP-001",
        tenant_id="tenant-demo",
        supplier="Security Provider",
        category="security",
        amount=18500,
        currency="ZAR",
        status="pending",
        recurring=True,
        frequency="monthly",
    )

    registry.register(expense)

    assert registry.get("EXP-001") == expense


def test_expense_registry_isolates_tenants():
    registry = ExpenseRegistry()

    registry.register(
        ExpenseRecord(
            expense_id="EXP-A",
            tenant_id="tenant-a",
            supplier="Supplier A",
            category="security",
            amount=1000,
            currency="ZAR",
            status="pending",
        )
    )

    registry.register(
        ExpenseRecord(
            expense_id="EXP-B",
            tenant_id="tenant-b",
            supplier="Supplier B",
            category="rent",
            amount=2000,
            currency="ZAR",
            status="pending",
        )
    )

    expenses = registry.list_for_tenant("tenant-a")

    assert [expense.expense_id for expense in expenses] == ["EXP-A"]


def test_expense_registry_rejects_duplicate_ids():
    registry = ExpenseRegistry()

    expense = ExpenseRecord(
        expense_id="EXP-DUP",
        tenant_id="tenant-demo",
        supplier="Supplier",
        category="internet",
        amount=500,
        currency="ZAR",
        status="pending",
    )

    registry.register(expense)

    try:
        registry.register(expense)
        assert False, "expected duplicate expense to be rejected"
    except ValueError as exc:
        assert "already registered" in str(exc)
