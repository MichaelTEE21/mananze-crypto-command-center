import pytest

from mananze_os.payment_confirmation import (
    PaymentConfirmation,
    assess_payment_confirmation,
)


def test_payment_confirmation_requires_identity():
    with pytest.raises(ValueError, match="confirmation_id is required"):
        PaymentConfirmation(
            confirmation_id="",
            tenant_id="tenant-1",
            quote_id="quote-1",
            status="confirmed",
        )


def test_payment_confirmation_requires_tenant():
    with pytest.raises(ValueError, match="tenant_id is required"):
        PaymentConfirmation(
            confirmation_id="payment-1",
            tenant_id="",
            quote_id="quote-1",
            status="confirmed",
        )


def test_payment_confirmation_requires_quote():
    with pytest.raises(ValueError, match="quote_id is required"):
        PaymentConfirmation(
            confirmation_id="payment-1",
            tenant_id="tenant-1",
            quote_id="",
            status="confirmed",
        )


def test_invalid_status_is_rejected():
    with pytest.raises(ValueError, match="invalid payment confirmation status"):
        PaymentConfirmation(
            confirmation_id="payment-1",
            tenant_id="tenant-1",
            quote_id="quote-1",
            status="invalid",
        )


def test_negative_amount_is_rejected():
    with pytest.raises(ValueError, match="amount cannot be negative"):
        PaymentConfirmation(
            confirmation_id="payment-1",
            tenant_id="tenant-1",
            quote_id="quote-1",
            status="confirmed",
            amount=-1,
        )


def test_confirmed_payment():
    result = assess_payment_confirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        evidence_ids=("pop-1",),
        evidence_sufficient=True,
        matches_quote=True,
        reference="POP123",
        amount=5000,
        currency="ZAR",
    )

    assert result.status == "confirmed"
    assert result.confirmed is True


def test_missing_evidence_requires_review():
    result = assess_payment_confirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        evidence_ids=(),
        evidence_sufficient=True,
        matches_quote=True,
    )

    assert result.status == "review_required"


def test_insufficient_evidence_requires_review():
    result = assess_payment_confirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        evidence_ids=("pop-1",),
        evidence_sufficient=False,
        matches_quote=True,
    )

    assert result.status == "review_required"


def test_mismatched_payment_requires_review():
    result = assess_payment_confirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        evidence_ids=("pop-1",),
        evidence_sufficient=True,
        matches_quote=False,
    )

    assert result.status == "review_required"


def test_payment_evidence_is_preserved():
    result = assess_payment_confirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        evidence_ids=("pop-1", "message-1"),
        evidence_sufficient=True,
        matches_quote=True,
    )

    assert result.evidence_ids == ("pop-1", "message-1")


def test_payment_confirmation_has_no_financial_system_dependency():
    result = assess_payment_confirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        evidence_ids=("pop-1",),
        evidence_sufficient=True,
        matches_quote=True,
    )

    assert result.confirmed is True
