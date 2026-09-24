from decimal import Decimal

from mananze_os.commercial_service import CommercialService
from mananze_os.economic_governor import (
    EconomicGovernor,
    PricingPolicy,
    ReferralPolicy,
    SubscriptionPlan,
)
from mananze_os.commercial_ledger import CommercialLedger


def test_commercial_service_subscription_billing_and_referral():
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

    ledger = CommercialLedger()

    service = CommercialService(
        economic_governor=EconomicGovernor(),
        ledger=ledger,
    )

    subscription = service.create_subscription(
        subscription_id="sub-001",
        tenant_id="tenant-001",
        plan=plan,
        subscription_level=2,
    )

    assert subscription.subscription_id == "sub-001"
    assert subscription.monthly_price == Decimal("1500.00")

    result = service.create_billing(
        billing_id="bill-001",
        tenant_id="tenant-001",
        plan=plan,
        billing_period="2026-09",
        usage_units=110,
        actual_provider_cost=Decimal("200.00"),
        pricing_policy=pricing,
    )

    assert result.billing.billing_id == "bill-001"
    assert result.billing.usage_amount == Decimal("50.00")
    assert result.billing.subscription_amount == Decimal("1500.00")
    assert result.billing.total_due == Decimal("1550.00")
    assert result.provider_charge == Decimal("350.00")
    assert result.billing_entry.amount_due == Decimal("1550.00")

    referral, referral_entry = service.create_referral(
        referral_id="ref-001",
        referrer_id="tenant-referrer",
        referred_tenant_id="tenant-001",
        plan=plan,
        subscription_level=2,
        qualifying_payment=Decimal("1500.00"),
        policy=referral_policy,
        qualifying_payment_id="payment-001",
    )

    assert referral.eligible is True
    assert referral.referrer_reward == Decimal("150.00")
    assert referral.customer_credit == Decimal("150.00")
    assert referral_entry is not None

    assert ledger.get_billing_entry("bill-001").amount_due == Decimal("1550.00")
    assert ledger.get_referral("ref-001").reward_amount == Decimal("150.00")
