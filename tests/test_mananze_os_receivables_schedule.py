from datetime import date
from decimal import Decimal

from mananze_os.receivables import (
    MandateStatus,
    PaymentMandate,
    build_installments,
    collectible_mandate,
)


def test_new_mandate_is_pending():
    mandate = PaymentMandate(
        mandate_id="mandate:1",
        tenant_id="tenant:1",
        borrower_id="borrower:1",
        account_id="account:1",
        provider_id="payments:test",
        authorization_reference="AUTH-001",
        amount=Decimal("800"),
    )

    assert mandate.status == MandateStatus.PENDING
    assert not mandate.is_collectible


def test_authorized_mandate_is_collectible():
    mandate = PaymentMandate(
        mandate_id="mandate:1",
        tenant_id="tenant:1",
        borrower_id="borrower:1",
        account_id="account:1",
        provider_id="payments:test",
        authorization_reference="AUTH-001",
        status=MandateStatus.AUTHORIZED,
        amount=Decimal("800"),
    )

    assert mandate.is_collectible
    assert collectible_mandate(mandate)


def test_rejected_mandate_is_not_collectible():
    mandate = PaymentMandate(
        mandate_id="mandate:1",
        tenant_id="tenant:1",
        borrower_id="borrower:1",
        account_id="account:1",
        provider_id="payments:test",
        authorization_reference="AUTH-001",
        status=MandateStatus.REJECTED,
        amount=Decimal("800"),
    )

    assert not collectible_mandate(mandate)


def test_build_monthly_installments():
    installments = build_installments(
        account_id="account:1",
        first_due_date=date(2026, 9, 30),
        amount=Decimal("800"),
        count=3,
    )

    assert len(installments) == 3
    assert installments[0].due_date == date(2026, 9, 30)
    assert installments[1].due_date == date(2026, 10, 30)
    assert installments[2].due_date == date(2026, 11, 30)


def test_schedule_handles_short_months():
    installments = build_installments(
        account_id="account:1",
        first_due_date=date(2026, 1, 31),
        amount=Decimal("500"),
        count=3,
    )

    assert installments[0].due_date == date(2026, 1, 31)
    assert installments[1].due_date == date(2026, 2, 28)
    assert installments[2].due_date == date(2026, 3, 31)
