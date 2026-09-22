"""Mananze OS recurring expense and obligation detection foundation."""

from dataclasses import dataclass
from typing import Literal

from mananze_os.payment_solution_intelligence import ExpenseRecord


PatternStatus = Literal[
    "unknown",
    "detected",
    "likely",
    "verified",
    "conflicting",
]


@dataclass(frozen=True)
class RecurringExpensePattern:
    tenant_id: str
    supplier: str
    category: str
    occurrence_count: int
    typical_amount: float
    currency: str
    frequency: str
    status: PatternStatus
    confidence: float
    evidence_expense_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.supplier.strip():
            raise ValueError("supplier is required")
        if not self.category.strip():
            raise ValueError("category is required")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be positive")
        if self.typical_amount < 0:
            raise ValueError("typical_amount cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")
        if not self.frequency.strip():
            raise ValueError("frequency is required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class ObligationCandidate:
    tenant_id: str
    name: str
    counterparty: str
    obligation_type: str
    amount: float | None
    currency: str | None
    frequency: str | None
    status: PatternStatus
    confidence: float
    evidence_expense_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.counterparty.strip():
            raise ValueError("counterparty is required")
        if not self.obligation_type.strip():
            raise ValueError("obligation_type is required")
        if self.amount is not None and self.amount < 0:
            raise ValueError("amount cannot be negative")
        if self.amount is not None and not self.currency:
            raise ValueError("currency is required when amount is provided")
        if self.currency is not None and not self.currency.strip():
            raise ValueError("currency cannot be empty")
        if self.frequency is not None and not self.frequency.strip():
            raise ValueError("frequency cannot be empty")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


class RecurringExpenseIntelligence:
    """Detect recurring expense patterns without creating authoritative obligations."""

    def detect(
        self,
        tenant_id: str,
        expenses: tuple[ExpenseRecord, ...],
    ) -> tuple[RecurringExpensePattern, ...]:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        tenant_expenses = tuple(
            expense
            for expense in expenses
            if expense.tenant_id == tenant_id
        )

        groups: dict[tuple[str, str, str], list[ExpenseRecord]] = {}

        for expense in tenant_expenses:
            if not expense.recurring:
                continue

            key = (
                expense.supplier,
                expense.category,
                expense.currency,
            )
            groups.setdefault(key, []).append(expense)

        patterns: list[RecurringExpensePattern] = []

        for (supplier, category, currency), group in sorted(groups.items()):
            amounts = [expense.amount for expense in group]
            typical_amount = sum(amounts) / len(amounts)

            if len(group) >= 3:
                status: PatternStatus = "likely"
                confidence = min(
                    0.95,
                    0.65 + (len(group) - 3) * 0.05,
                )
            elif len(group) == 2:
                status = "detected"
                confidence = 0.55
            else:
                status = "detected"
                confidence = 0.35

            frequency_values = {
                expense.frequency
                for expense in group
                if expense.frequency
            }

            frequency = (
                next(iter(frequency_values))
                if len(frequency_values) == 1
                else "unknown"
            )

            patterns.append(
                RecurringExpensePattern(
                    tenant_id=tenant_id,
                    supplier=supplier,
                    category=category,
                    occurrence_count=len(group),
                    typical_amount=typical_amount,
                    currency=currency,
                    frequency=frequency,
                    status=status,
                    confidence=confidence,
                    evidence_expense_ids=tuple(
                        expense.expense_id for expense in group
                    ),
                )
            )

        return tuple(patterns)

    def build_candidates(
        self,
        patterns: tuple[RecurringExpensePattern, ...],
    ) -> tuple[ObligationCandidate, ...]:
        candidates: list[ObligationCandidate] = []

        for pattern in patterns:
            if pattern.status == "conflicting":
                continue

            candidates.append(
                ObligationCandidate(
                    tenant_id=pattern.tenant_id,
                    name=f"{pattern.supplier} - {pattern.category}",
                    counterparty=pattern.supplier,
                    obligation_type="expense",
                    amount=pattern.typical_amount,
                    currency=pattern.currency,
                    frequency=pattern.frequency,
                    status=pattern.status,
                    confidence=pattern.confidence,
                    evidence_expense_ids=pattern.evidence_expense_ids,
                )
            )

        return tuple(candidates)


__all__ = [
    "PatternStatus",
    "RecurringExpensePattern",
    "ObligationCandidate",
    "RecurringExpenseIntelligence",
]
