from decimal import Decimal

import pytest

from mananze_os.economic_governor import (
    EconomicGovernor,
    PricingPolicy,
    ReferralPolicy,
    SubscriptionPlan,
)


def test_usage_above_included_units_is_charged():
    governor = EconomicGovernor()

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
        included_usage_units=100,
        overage_price_per_unit=Decimal("2.50"),
    )

    assert governor.calculate_usage_charge(
        plan=plan,
        usage_units=120,
    ) == Decimal("50.00")


def test_actual_cost_can_be_marked_up():
    governor = EconomicGovernor()

    result = governor.calculate_cost_charge(
        actual_cost=Decimal("3.00"),
        policy=PricingPolicy(
            policy_id="standard",
            markup_rate=Decimal("0.50"),
        ),
    )

    assert result == Decimal("4.50")


def test_referral_requires_eligible_subscription_and_payment():
    governor = EconomicGovernor()

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
    )

    referral = governor.calculate_referral(
        referral_id="ref-001",
        referrer_id="user-001",
        referred_tenant_id="tenant-001",
        plan=plan,
        subscription_level=2,
        qualifying_payment=Decimal("1500.00"),
        policy=ReferralPolicy(
            policy_id="standard-referral",
            minimum_subscription_level=2,
        ),
    )

    assert referral.eligible is True
    assert referral.referrer_reward == Decimal("150.00")
    assert referral.customer_credit == Decimal("150.00")
    assert referral.status == "confirmed"


def test_signup_alone_does_not_trigger_referral():
    governor = EconomicGovernor()

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
    )

    referral = governor.calculate_referral(
        referral_id="ref-002",
        referrer_id="user-001",
        referred_tenant_id="tenant-002",
        plan=plan,
        subscription_level=2,
        qualifying_payment=Decimal("0.00"),
        policy=ReferralPolicy(
            policy_id="standard-referral",
            minimum_subscription_level=2,
        ),
    )

    assert referral.eligible is False
    assert referral.referrer_reward == Decimal("0.00")
    assert referral.customer_credit == Decimal("0.00")


def test_lower_subscription_level_does_not_trigger_referral():
    governor = EconomicGovernor()

    plan = SubscriptionPlan(
        plan_id="level-1",
        name="Level 1",
        monthly_price=Decimal("500.00"),
    )

    referral = governor.calculate_referral(
        referral_id="ref-003",
        referrer_id="user-001",
        referred_tenant_id="tenant-003",
        plan=plan,
        subscription_level=1,
        qualifying_payment=Decimal("500.00"),
        policy=ReferralPolicy(
            policy_id="standard-referral",
            minimum_subscription_level=2,
        ),
    )

    assert referral.eligible is False


def test_billing_applies_customer_referral_credit():
    governor = EconomicGovernor()

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
        included_usage_units=100,
        overage_price_per_unit=Decimal("2.00"),
    )

    billing = governor.create_billing_record(
        billing_id="bill-001",
        tenant_id="tenant-001",
        plan=plan,
        usage_units=110,
        referral_credit=Decimal("150.00"),
    )

    assert billing.subscription_amount == Decimal("1500.00")
    assert billing.usage_amount == Decimal("20.00")
    assert billing.referral_credit == Decimal("150.00")
    assert billing.total_due == Decimal("1370.00")


def test_negative_values_are_rejected():
    governor = EconomicGovernor()

    with pytest.raises(ValueError):
        governor.calculate_usage_charge(
            plan=SubscriptionPlan(
                plan_id="level-1",
                name="Level 1",
                monthly_price=Decimal("500.00"),
            ),
            usage_units=-1,
        )
