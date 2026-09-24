from decimal import Decimal

from mananze_os.commercial_ledger import (
    BillingLedgerEntry,
    CommercialLedger,
    ReferralLedgerEntry,
    SubscriptionRecord,
)
from mananze_os.economic_governor import (
    EconomicGovernor,
    PricingPolicy,
    ReferralPolicy,
    SubscriptionPlan,
)
from mananze_os.sqlite_commercial_store import SQLiteCommercialStore


def test_economic_to_commercial_to_sqlite(tmp_path):
    db_path = tmp_path / "commercial.db"

    governor = EconomicGovernor()
    ledger = CommercialLedger()
    store = SQLiteCommercialStore(db_path)

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
        minimum_referral_level=2,
        included_usage_units=100,
        overage_price_per_unit=Decimal("5.00"),
    )

    pricing = PricingPolicy(
        policy_id="standard-margin",
        markup_rate=Decimal("0.75"),
        minimum_charge=Decimal("0.00"),
    )

    referral_policy = ReferralPolicy(
        policy_id="standard-referral",
        minimum_subscription_level=2,
        referrer_rate=Decimal("0.10"),
        customer_rate=Decimal("0.10"),
    )

    usage_charge = governor.calculate_usage_charge(
        plan=plan,
        usage_units=110,
    )

    provider_charge = governor.calculate_cost_charge(
        actual_cost=Decimal("3.40"),
        policy=pricing,
    )

    referral = governor.calculate_referral(
        referral_id="ref-001",
        referrer_id="tenant-referrer",
        referred_tenant_id="tenant-001",
        plan=plan,
        subscription_level=2,
        qualifying_payment=Decimal("1500.00"),
        policy=referral_policy,
    )

    billing = governor.create_billing_record(
        billing_id="bill-001",
        tenant_id="tenant-001",
        plan=plan,
        usage_units=110,
        referral_credit=referral.customer_credit,
    )

    subscription = SubscriptionRecord(
        subscription_id="sub-001",
        tenant_id="tenant-001",
        plan_id=plan.plan_id,
        subscription_level=2,
        monthly_price=plan.monthly_price,
        currency="ZAR",
        status="active",
    )

    billing_entry = BillingLedgerEntry(
        billing_id=billing.billing_id,
        tenant_id=billing.tenant_id,
        billing_period="2026-09",
        amount_due=billing.total_due,
        currency=billing.currency,
        status="pending",
    )

    referral_entry = ReferralLedgerEntry(
        referral_id=referral.referral_id,
        qualifying_payment_id="payment-001",
        referrer_id=referral.referrer_id,
        referred_tenant_id=referral.referred_tenant_id,
        reward_amount=referral.referrer_reward,
        customer_credit=referral.customer_credit,
        currency="ZAR",
        status="pending",
    )

    ledger.add_subscription(subscription)
    ledger.add_billing_entry(billing_entry)
    ledger.add_referral(referral_entry)

    store.add_subscription(subscription)
    store.add_billing_entry(billing_entry)
    store.add_referral(referral_entry)

    assert usage_charge == Decimal("50.00")
    assert provider_charge == Decimal("5.95")

    assert referral.eligible is True
    assert referral.referrer_reward == Decimal("150.00")
    assert referral.customer_credit == Decimal("150.00")

    persisted_subscription = store.get_subscription("sub-001")
    persisted_billing = store.get_billing_entry("bill-001")
    persisted_referral = store.get_referral("ref-001")

    assert persisted_subscription is not None
    assert persisted_billing is not None
    assert persisted_referral is not None

    assert persisted_subscription.tenant_id == "tenant-001"
    assert persisted_billing.amount_due == billing.total_due
    assert persisted_referral.customer_credit == Decimal("150.00")


def test_commercial_state_survives_store_restart(tmp_path):
    db_path = tmp_path / "commercial.db"

    subscription = SubscriptionRecord(
        subscription_id="sub-restart",
        tenant_id="tenant-restart",
        plan_id="level-2",
        subscription_level=2,
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
        status="active",
    )

    first_store = SQLiteCommercialStore(db_path)
    first_store.add_subscription(subscription)

    second_store = SQLiteCommercialStore(db_path)

    restored = second_store.get_subscription("sub-restart")

    assert restored is not None
    assert restored.subscription_id == "sub-restart"
    assert restored.tenant_id == "tenant-restart"
    assert restored.monthly_price == Decimal("1500.00")



