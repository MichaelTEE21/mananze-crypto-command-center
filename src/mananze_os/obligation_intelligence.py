"""Mananze OS obligation intelligence foundation."""

from dataclasses import dataclass
from typing import Literal


ObligationStatus = Literal[
    "identified",
    "pending",
    "active",
    "due",
    "overdue",
    "completed",
    "cancelled",
]


ObligationType = Literal[
    "expense",
    "contract",
    "subscription",
    "lease",
    "insurance",
    "finance",
    "payroll",
    "tax",
    "licence",
    "maintenance",
    "supplier",
    "service",
    "other",
]


@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    tenant_id: str
    name: str
    obligation_type: ObligationType
    counterparty: str
    amount: float | None = None
    currency: str | None = None
    frequency: str | None = None
    due_date: str | None = None
    renewal_date: str | None = None
    status: ObligationStatus = "identified"
    approval_required: bool = True
    source_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.obligation_id.strip():
            raise ValueError("obligation_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.name.strip():
            raise ValueError("name is required")

        if not self.obligation_type.strip():
            raise ValueError("obligation_type is required")

        if not self.counterparty.strip():
            raise ValueError("counterparty is required")

        if self.amount is not None and self.amount < 0:
            raise ValueError("amount cannot be negative")

        if self.amount is not None and not self.currency:
            raise ValueError(
                "currency is required when amount is provided"
            )

        if self.currency is not None and not self.currency.strip():
            raise ValueError("currency cannot be empty")

        if self.frequency is not None and not self.frequency.strip():
            raise ValueError("frequency cannot be empty")

        if self.due_date is not None and not self.due_date.strip():
            raise ValueError("due_date cannot be empty")

        if self.renewal_date is not None and not self.renewal_date.strip():
            raise ValueError("renewal_date cannot be empty")

        if (
            self.source_reference is not None
            and not self.source_reference.strip()
        ):
            raise ValueError("source_reference cannot be empty")


@dataclass(frozen=True)
class ObligationDependency:
    dependency_id: str
    tenant_id: str
    obligation_id: str
    depends_on: str
    impact: str

    def __post_init__(self) -> None:
        if not self.dependency_id.strip():
            raise ValueError("dependency_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.obligation_id.strip():
            raise ValueError("obligation_id is required")

        if not self.depends_on.strip():
            raise ValueError("depends_on is required")

        if not self.impact.strip():
            raise ValueError("impact is required")


__all__ = [
    "ObligationStatus",
    "ObligationType",
    "Obligation",
    "ObligationDependency",
]
