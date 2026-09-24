from decimal import Decimal

import pytest

from mananze_os.commercial_ledger import (
    BillingLedgerEntry,
    CommercialLedger,
    ReferralLedgerEntry,
    SubscriptionRecord,
)


def test_subscription_is_recorded():
    ledger = CommercialLedger()

    subscription = ledger.add_subscription(
        SubscriptionRecord(
            subscription_id="sub-001",
            tenant_id="tenant-001",
            plan_id="level-2",
            subscription_level=2,
            monthly_price=Decimal("1500.00"),
            currency="ZAR",
        )
    )

    assert ledger.get_subscription("sub-001") == subscription


def test_billing_payment_is_idempotent():
    ledger = CommercialLedger()

    ledger.add_billing_entry(
        BillingLedgerEntry(
            billing_id="bill-001",
            tenant_id="tenant-001",
            billing_period="2026-09",
            amount_due=Decimal("1500.00"),
            currency="ZAR",
        )
    )

    first = ledger.confirm_payment(
        billing_id="bill-001",
        payment_id="payment-001",
    )

    second = ledger.confirm_payment(
        billing_id="bill-001",
        payment_id="payment-001",
    )

    assert first == second
    assert second.status == "paid"


def test_same_payment_cannot_be_used_for_two_bills():
    ledger = CommercialLedger()

    for billing_id in ("bill-001", "bill-002"):
        ledger.add_billing_entry(
            BillingLedgerEntry(
                billing_id=billing_id,
                tenant_id="tenant-001",
                billing_period=billing_id,
                amount_due=Decimal("1500.00"),
                currency="ZAR",
            )
        )

    ledger.confirm_payment(
        billing_id="bill-001",
        payment_id="payment-001",
    )

    with pytest.raises(ValueError, match="payment already processed"):
        ledger.confirm_payment(
            billing_id="bill-002",
            payment_id="payment-001",
        )


def test_referral_payment_can_only_trigger_one_reward():
    ledger = CommercialLedger()

    ledger.add_referral(
        ReferralLedgerEntry(
            referral_id="ref-001",
            qualifying_payment_id="payment-001",
            referrer_id="user-001",
            referred_tenant_id="tenant-002",
            reward_amount=Decimal("150.00"),
            customer_credit=Decimal("150.00"),
            currency="ZAR",
        )
    )

    with pytest.raises(ValueError, match="qualifying payment already"):
        ledger.add_referral(
            ReferralLedgerEntry(
                referral_id="ref-002",
                qualifying_payment_id="payment-001",
                referrer_id="user-002",
                referred_tenant_id="tenant-003",
                reward_amount=Decimal("150.00"),
                customer_credit=Decimal("150.00"),
                currency="ZAR",
            )
        )


def test_duplicate_subscription_is_rejected():
    ledger = CommercialLedger()

    subscription = SubscriptionRecord(
        subscription_id="sub-001",
        tenant_id="tenant-001",
        plan_id="level-2",
        subscription_level=2,
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
    )

    ledger.add_subscription(subscription)

    with pytest.raises(ValueError, match="subscription already exists"):
        ledger.add_subscription(subscription)
