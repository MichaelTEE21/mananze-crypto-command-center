"""Mananze OS payment and expense solution intelligence foundation."""

from dataclasses import dataclass
from typing import Literal


PaymentStatus = Literal[
    "pending",
    "paid",
    "failed",
    "reversed",
    "refunded",
    "cancelled",
]

ExpenseStatus = Literal[
    "identified",
    "pending",
    "approved",
    "paid",
    "overdue",
    "cancelled",
]


@dataclass(frozen=True)
class PaymentMethod:
    payment_method_id: str
    name: str
    method_type: str
    provider: str | None = None

    def __post_init__(self) -> None:
        if not self.payment_method_id.strip():
            raise ValueError("payment_method_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.method_type.strip():
            raise ValueError("method_type is required")


@dataclass(frozen=True)
class PaymentEvent:
    payment_id: str
    tenant_id: str
    amount: float
    currency: str
    status: PaymentStatus
    payment_method_id: str | None = None
    reference: str | None = None

    def __post_init__(self) -> None:
        if not self.payment_id.strip():
            raise ValueError("payment_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if self.amount < 0:
            raise ValueError("amount cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")


@dataclass(frozen=True)
class ExpenseRecord:
    expense_id: str
    tenant_id: str
    supplier: str
    category: str
    amount: float
    currency: str
    status: ExpenseStatus
    recurring: bool = False
    frequency: str | None = None
    due_date: str | None = None
    approval_required: bool = True

    def __post_init__(self) -> None:
        if not self.expense_id.strip():
            raise ValueError("expense_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.supplier.strip():
            raise ValueError("supplier is required")
        if not self.category.strip():
            raise ValueError("category is required")
        if self.amount < 0:
            raise ValueError("amount cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")

        if self.recurring and not self.frequency:
            raise ValueError(
                "frequency is required for recurring expenses"
            )


@dataclass(frozen=True)
class ExpenseAssessment:
    expense_id: str
    category: str
    recurring: bool
    approval_required: bool
    automation_candidate: bool
    reason: str
    due_date: str | None = None
    payment_status: ExpenseStatus = "identified"


@dataclass(frozen=True)
class ExpensePortfolioAssessment:
    tenant_id: str
    expense_count: int
    recurring_expense_count: int
    pending_expense_count: int
    overdue_expense_count: int
    total_value: float
    recurring_value: float
    categories: tuple[str, ...]


class PaymentSolutionIntelligence:
    """Analyse authorised payment and expense information.

    This layer analyses payment infrastructure and expenses. It does not
    authorise itself, move money, or bypass financial governance.
    """

    def assess_expense(
        self,
        expense: ExpenseRecord,
    ) -> ExpenseAssessment:
        if not expense.expense_id.strip():
            raise ValueError("expense_id is required")

        if expense.status == "cancelled":
            return ExpenseAssessment(
                expense_id=expense.expense_id,
                category=expense.category,
                recurring=expense.recurring,
                approval_required=expense.approval_required,
                automation_candidate=False,
                reason="cancelled expense",
                due_date=expense.due_date,
                payment_status=expense.status,
            )

        automation_candidate = (
            expense.recurring
            and expense.approval_required
            and expense.status in {
                "identified",
                "pending",
                "approved",
                "paid",
                "overdue",
            }
        )

        if automation_candidate:
            reason = (
                "recurring expense can be considered for governed "
                "approval and payment automation"
            )
        else:
            reason = (
                "expense requires normal governed processing "
                "or additional information"
            )

        return ExpenseAssessment(
            expense_id=expense.expense_id,
            category=expense.category,
            recurring=expense.recurring,
            approval_required=expense.approval_required,
            automation_candidate=automation_candidate,
            reason=reason,
            due_date=expense.due_date,
            payment_status=expense.status,
        )

    def assess_portfolio(
        self,
        tenant_id: str,
        expenses: tuple[ExpenseRecord, ...],
    ) -> ExpensePortfolioAssessment:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        tenant_expenses = tuple(
            expense
            for expense in expenses
            if expense.tenant_id == tenant_id
        )

        categories = tuple(
            sorted(
                {
                    expense.category
                    for expense in tenant_expenses
                }
            )
        )

        return ExpensePortfolioAssessment(
            tenant_id=tenant_id,
            expense_count=len(tenant_expenses),
            recurring_expense_count=sum(
                expense.recurring
                for expense in tenant_expenses
            ),
            pending_expense_count=sum(
                expense.status in {"identified", "pending", "approved"}
                for expense in tenant_expenses
            ),
            overdue_expense_count=sum(
                expense.status == "overdue"
                for expense in tenant_expenses
            ),
            total_value=sum(
                expense.amount
                for expense in tenant_expenses
            ),
            recurring_value=sum(
                expense.amount
                for expense in tenant_expenses
                if expense.recurring
            ),
            categories=categories,
        )


__all__ = [
    "PaymentStatus",
    "ExpenseStatus",
    "PaymentMethod",
    "PaymentEvent",
    "ExpenseRecord",
    "ExpenseAssessment",
    "ExpensePortfolioAssessment",
    "PaymentSolutionIntelligence",
]
