from datetime import date
from decimal import Decimal

import pytest

from mananze_os.receivables import (
    Borrower,
    Installment,
    Payment,
    ReceivableAccount,
    Reminder,
    outstanding_balance,
)


def test_borrower_requires_identity():
    borrower = Borrower(
        borrower_id="borrower:1",
        tenant_id="tenant:1",
        name="Thabo",
        contact="+27820000000",
    )

    assert borrower.name == "Thabo"


def test_receivable_account_preserves_agreed_total():
    account = ReceivableAccount(
        account_id="account:1",
        tenant_id="tenant:1",
        borrower_id="borrower:1",
        principal=Decimal("2000"),
        agreed_total=Decimal("2400"),
    )

    assert account.agreed_total == Decimal("2400")


def test_installment_cannot_be_overpaid():
    with pytest.raises(ValueError, match="cannot exceed"):
        Installment(
            installment_id="installment:1",
            account_id="account:1",
            due_date=date(2026, 10, 30),
            amount=Decimal("800"),
            paid_amount=Decimal("801"),
        )


def test_payment_must_be_positive():
    with pytest.raises(ValueError, match="must be positive"):
        Payment(
            payment_id="payment:1",
            tenant_id="tenant:1",
            account_id="account:1",
            amount=Decimal("0"),
            payment_date=date(2026, 9, 25),
        )


def test_outstanding_balance_uses_agreed_total():
    account = ReceivableAccount(
        account_id="account:1",
        tenant_id="tenant:1",
        borrower_id="borrower:1",
        principal=Decimal("2000"),
        agreed_total=Decimal("2400"),
    )

    payments = (
        Payment(
            payment_id="payment:1",
            tenant_id="tenant:1",
            account_id="account:1",
            amount=Decimal("800"),
            payment_date=date(2026, 9, 25),
        ),
    )

    assert outstanding_balance(account, payments) == Decimal("1600")


def test_outstanding_balance_rejects_cross_tenant_payment():
    account = ReceivableAccount(
        account_id="account:1",
        tenant_id="tenant:1",
        borrower_id="borrower:1",
        principal=Decimal("2000"),
        agreed_total=Decimal("2400"),
    )

    payment = Payment(
        payment_id="payment:1",
        tenant_id="tenant:2",
        account_id="account:1",
        amount=Decimal("800"),
        payment_date=date(2026, 9, 25),
    )

    with pytest.raises(ValueError, match="tenant mismatch"):
        outstanding_balance(account, (payment,))


def test_reminder_requires_message():
    with pytest.raises(ValueError, match="message is required"):
        Reminder(
            reminder_id="reminder:1",
            tenant_id="tenant:1",
            account_id="account:1",
            installment_id="installment:1",
            channel="whatsapp",
            message="",
            scheduled_for=date(2026, 10, 28),
        )
