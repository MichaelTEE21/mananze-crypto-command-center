from decimal import Decimal

import pytest

from mananze_os.commercial_ledger import (
    BillingLedgerEntry,
    ReferralLedgerEntry,
    SubscriptionRecord,
)
from mananze_os.sqlite_commercial_store import SQLiteCommercialStore


def test_subscription_survives_store_restart(tmp_path):
    db = tmp_path / "commercial.db"

    store = SQLiteCommercialStore(db)
    subscription = SubscriptionRecord(
        subscription_id="sub-001",
        tenant_id="tenant-001",
        plan_id="level-2",
        subscription_level=2,
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
    )
    store.add_subscription(subscription)

    restarted = SQLiteCommercialStore(db)

    assert restarted.get_subscription("sub-001") == subscription


def test_billing_survives_store_restart(tmp_path):
    db = tmp_path / "commercial.db"

    store = SQLiteCommercialStore(db)
    entry = BillingLedgerEntry(
        billing_id="bill-001",
        tenant_id="tenant-001",
        billing_period="2026-09",
        amount_due=Decimal("1500.00"),
        currency="ZAR",
    )
    store.add_billing_entry(entry)

    restarted = SQLiteCommercialStore(db)

    assert restarted.get_billing_entry("bill-001") == entry


def test_payment_confirmation_is_durable_and_idempotent(tmp_path):
    db = tmp_path / "commercial.db"

    store = SQLiteCommercialStore(db)
    store.add_billing_entry(
        BillingLedgerEntry(
            billing_id="bill-001",
            tenant_id="tenant-001",
            billing_period="2026-09",
            amount_due=Decimal("1500.00"),
            currency="ZAR",
        )
    )

    first = store.confirm_payment(
        billing_id="bill-001",
        payment_id="payment-001",
    )

    restarted = SQLiteCommercialStore(db)

    second = restarted.confirm_payment(
        billing_id="bill-001",
        payment_id="payment-001",
    )

    assert first == second
    assert second.status == "paid"


def test_payment_cannot_pay_two_bills(tmp_path):
    db = tmp_path / "commercial.db"

    store = SQLiteCommercialStore(db)

    for billing_id in ("bill-001", "bill-002"):
        store.add_billing_entry(
            BillingLedgerEntry(
                billing_id=billing_id,
                tenant_id="tenant-001",
                billing_period=billing_id,
                amount_due=Decimal("1500.00"),
                currency="ZAR",
            )
        )

    store.confirm_payment(
        billing_id="bill-001",
        payment_id="payment-001",
    )

    with pytest.raises(ValueError, match="payment already processed"):
        store.confirm_payment(
            billing_id="bill-002",
            payment_id="payment-001",
        )


def test_referral_survives_restart_and_payment_is_unique(tmp_path):
    db = tmp_path / "commercial.db"

    store = SQLiteCommercialStore(db)

    referral = ReferralLedgerEntry(
        referral_id="ref-001",
        qualifying_payment_id="payment-001",
        referrer_id="user-001",
        referred_tenant_id="tenant-002",
        reward_amount=Decimal("150.00"),
        customer_credit=Decimal("150.00"),
        currency="ZAR",
    )

    store.add_referral(referral)

    restarted = SQLiteCommercialStore(db)

    assert restarted.get_referral("ref-001") == referral

    with pytest.raises(
        ValueError,
        match="qualifying payment already",
    ):
        restarted.add_referral(
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


def test_tenant_scoped_reads(tmp_path):
    db = tmp_path / "commercial.db"

    store = SQLiteCommercialStore(db)

    for tenant_id, subscription_id in (
        ("tenant-001", "sub-001"),
        ("tenant-002", "sub-002"),
    ):
        store.add_subscription(
            SubscriptionRecord(
                subscription_id=subscription_id,
                tenant_id=tenant_id,
                plan_id="level-2",
                subscription_level=2,
                monthly_price=Decimal("1500.00"),
                currency="ZAR",
            )
        )

    tenant_one = store.list_subscriptions("tenant-001")

    assert len(tenant_one) == 1
    assert tenant_one[0].tenant_id == "tenant-001"
    assert tenant_one[0].subscription_id == "sub-001"


def test_duplicate_subscription_is_rejected(tmp_path):
    db = tmp_path / "commercial.db"

    store = SQLiteCommercialStore(db)

    subscription = SubscriptionRecord(
        subscription_id="sub-001",
        tenant_id="tenant-001",
        plan_id="level-2",
        subscription_level=2,
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
    )

    store.add_subscription(subscription)

    with pytest.raises(
        ValueError,
        match="subscription already exists",
    ):
        store.add_subscription(subscription)
