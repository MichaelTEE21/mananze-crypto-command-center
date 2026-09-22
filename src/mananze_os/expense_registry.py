"""Mananze OS payment and expense registry."""

from mananze_os.payment_solution_intelligence import ExpenseRecord


class ExpenseRegistry:
    """Tenant-aware registry for authorised expense records."""

    def __init__(self) -> None:
        self._expenses: dict[str, ExpenseRecord] = {}

    def register(self, expense: ExpenseRecord) -> None:
        existing = self._expenses.get(expense.expense_id)

        if existing is not None:
            raise ValueError(
                f"expense already registered: {expense.expense_id}"
            )

        self._expenses[expense.expense_id] = expense

    def get(self, expense_id: str) -> ExpenseRecord:
        if not expense_id.strip():
            raise ValueError("expense_id is required")

        try:
            return self._expenses[expense_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown expense: {expense_id}"
            ) from exc

    def list_for_tenant(self, tenant_id: str) -> tuple[ExpenseRecord, ...]:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        return tuple(
            expense
            for expense in self._expenses.values()
            if expense.tenant_id == tenant_id
        )

    def list_all(self) -> tuple[ExpenseRecord, ...]:
        return tuple(self._expenses.values())


__all__ = ["ExpenseRegistry"]
