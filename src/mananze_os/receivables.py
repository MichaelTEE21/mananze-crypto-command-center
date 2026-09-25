"""MANANZE OS receivables and repayment domain contracts.

This module models receivables and repayment state only.
It does not send communications, execute payments, grant authority,
or make collection decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


ReceivableStatus = Literal[
    "active",
    "paid",
    "overdue",
    "disputed",
    "cancelled",
]

InstallmentStatus = Literal[
    "scheduled",
    "due",
    "paid",
    "partial",
    "overdue",
    "disputed",
]


@dataclass(frozen=True)
class Borrower:
    borrower_id: str
    tenant_id: str
    name: str
    contact: str

    def __post_init__(self) -> None:
        if not self.borrower_id.strip():
            raise ValueError("borrower_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.name.strip():
            raise ValueError("borrower name is required")
        if not self.contact.strip():
            raise ValueError("borrower contact is required")


@dataclass(frozen=True)
class ReceivableAccount:
    account_id: str
    tenant_id: str
    borrower_id: str
    principal: Decimal
    agreed_total: Decimal
    status: ReceivableStatus = "active"

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError("account_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.borrower_id.strip():
            raise ValueError("borrower_id is required")
        if self.principal < Decimal("0"):
            raise ValueError("principal cannot be negative")
        if self.agreed_total < Decimal("0"):
            raise ValueError("agreed_total cannot be negative")


@dataclass(frozen=True)
class Installment:
    installment_id: str
    account_id: str
    due_date: date
    amount: Decimal
    status: InstallmentStatus = "scheduled"
    paid_amount: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.installment_id.strip():
            raise ValueError("installment_id is required")
        if not self.account_id.strip():
            raise ValueError("account_id is required")
        if self.amount <= Decimal("0"):
            raise ValueError("installment amount must be positive")
        if self.paid_amount < Decimal("0"):
            raise ValueError("paid_amount cannot be negative")
        if self.paid_amount > self.amount:
            raise ValueError("paid_amount cannot exceed installment amount")


@dataclass(frozen=True)
class Payment:
    payment_id: str
    tenant_id: str
    account_id: str
    amount: Decimal
    payment_date: date
    reference: str = ""

    def __post_init__(self) -> None:
        if not self.payment_id.strip():
            raise ValueError("payment_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.account_id.strip():
            raise ValueError("account_id is required")
        if self.amount <= Decimal("0"):
            raise ValueError("payment amount must be positive")


@dataclass(frozen=True)
class MandateStatus:
    PENDING = "pending"
    AUTHORIZED = "authorized"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass(frozen=True)
class PaymentMandate:
    mandate_id: str
    tenant_id: str
    borrower_id: str
    account_id: str
    provider_id: str
    authorization_reference: str
    status: str = MandateStatus.PENDING
    frequency: str = "monthly"
    amount: Decimal = Decimal("0")
    effective_date: date | None = None
    expiry_date: date | None = None
    evidence_reference: str = ""

    def __post_init__(self) -> None:
        if not self.mandate_id.strip():
            raise ValueError("mandate_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.borrower_id.strip():
            raise ValueError("borrower_id is required")
        if not self.account_id.strip():
            raise ValueError("account_id is required")
        if not self.provider_id.strip():
            raise ValueError("provider_id is required")
        if not self.authorization_reference.strip():
            raise ValueError("authorization_reference is required")
        if self.amount < Decimal("0"):
            raise ValueError("mandate amount cannot be negative")

    @property
    def is_collectible(self) -> bool:
        return self.status == MandateStatus.AUTHORIZED


def build_installments(
    *,
    account_id: str,
    first_due_date: date,
    amount: Decimal,
    count: int,
) -> tuple[Installment, ...]:
    if not account_id.strip():
        raise ValueError("account_id is required")

    if amount <= Decimal("0"):
        raise ValueError("installment amount must be positive")

    if count <= 0:
        raise ValueError("count must be positive")

    installments: list[Installment] = []

    year = first_due_date.year
    month = first_due_date.month

    for index in range(count):
        month_offset = month - 1 + index
        due_year = year + month_offset // 12
        due_month = month_offset % 12 + 1

        # Keep the requested day when possible. If the month is shorter,
        # use its final valid day.
        import calendar

        due_day = min(
            first_due_date.day,
            calendar.monthrange(due_year, due_month)[1],
        )

        due_date = date(due_year, due_month, due_day)

        installments.append(
            Installment(
                installment_id=f"{account_id}:installment:{index + 1}",
                account_id=account_id,
                due_date=due_date,
                amount=amount,
            )
        )

    return tuple(installments)


def collectible_mandate(mandate: PaymentMandate) -> bool:
    return mandate.is_collectible


@dataclass(frozen=True)
class Reminder:
    reminder_id: str
    tenant_id: str
    account_id: str
    installment_id: str
    channel: str
    message: str
    scheduled_for: date

    def __post_init__(self) -> None:
        if not self.reminder_id.strip():
            raise ValueError("reminder_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.account_id.strip():
            raise ValueError("account_id is required")
        if not self.installment_id.strip():
            raise ValueError("installment_id is required")
        if not self.channel.strip():
            raise ValueError("channel is required")
        if not self.message.strip():
            raise ValueError("message is required")


def outstanding_balance(
    account: ReceivableAccount,
    payments: tuple[Payment, ...],
) -> Decimal:
    if any(payment.tenant_id != account.tenant_id for payment in payments):
        raise ValueError("payment tenant mismatch")

    if any(payment.account_id != account.account_id for payment in payments):
        raise ValueError("payment account mismatch")

    paid = sum(
        (payment.amount for payment in payments),
        Decimal("0"),
    )

    balance = account.agreed_total - paid
    return max(balance, Decimal("0"))


__all__ = [
    "Borrower",
    "MandateStatus",
    "PaymentMandate",
    "Installment",
    "InstallmentStatus",
    "Payment",
    "ReceivableAccount",
    "ReceivableStatus",
    "Reminder",
    "build_installments",
    "collectible_mandate",
    "outstanding_balance",
]
