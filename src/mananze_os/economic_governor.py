"""Central economic governance for Mananze OS.

Calculates client pricing, subscription charges, usage charges, and
verified referral rewards. This module does not move money or grant
execution authority.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal


BillingStatus = Literal["draft", "pending", "paid", "cancelled"]
ReferralStatus = Literal["pending", "confirmed", "paid", "rejected"]


def _money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


@dataclass(frozen=True)
class SubscriptionPlan:
    plan_id: str
    name: str
    monthly_price: Decimal
    currency: str = "ZAR"
    minimum_referral_level: int | None = None
    included_usage_units: int = 0
    overage_price_per_unit: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        if not self.plan_id.strip():
            raise ValueError("plan_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if self.monthly_price < 0:
            raise ValueError("monthly_price cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")
        if self.minimum_referral_level is not None:
            if self.minimum_referral_level < 1:
                raise ValueError("minimum_referral_level must be positive")
        if self.included_usage_units < 0:
            raise ValueError("included_usage_units cannot be negative")
        if self.overage_price_per_unit < 0:
            raise ValueError("overage_price_per_unit cannot be negative")


@dataclass(frozen=True)
class PricingPolicy:
    policy_id: str
    markup_rate: Decimal = Decimal("0.00")
    minimum_charge: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id is required")
        if self.markup_rate < 0:
            raise ValueError("markup_rate cannot be negative")
        if self.minimum_charge < 0:
            raise ValueError("minimum_charge cannot be negative")


@dataclass(frozen=True)
class ReferralPolicy:
    policy_id: str
    minimum_subscription_level: int
    referrer_rate: Decimal = Decimal("0.10")
    customer_rate: Decimal = Decimal("0.10")

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id is required")
        if self.minimum_subscription_level < 1:
            raise ValueError("minimum_subscription_level must be positive")
        if not 0 <= self.referrer_rate <= 1:
            raise ValueError("referrer_rate must be between 0 and 1")
        if not 0 <= self.customer_rate <= 1:
            raise ValueError("customer_rate must be between 0 and 1")


@dataclass(frozen=True)
class BillingRecord:
    billing_id: str
    tenant_id: str
    plan_id: str
    subscription_amount: Decimal
    usage_amount: Decimal
    referral_credit: Decimal
    total_due: Decimal
    currency: str
    status: BillingStatus = "draft"

    def __post_init__(self) -> None:
        if not self.billing_id.strip():
            raise ValueError("billing_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.plan_id.strip():
            raise ValueError("plan_id is required")
        if self.subscription_amount < 0:
            raise ValueError("subscription_amount cannot be negative")
        if self.usage_amount < 0:
            raise ValueError("usage_amount cannot be negative")
        if self.referral_credit < 0:
            raise ValueError("referral_credit cannot be negative")
        if self.total_due < 0:
            raise ValueError("total_due cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")


@dataclass(frozen=True)
class ReferralRecord:
    referral_id: str
    referrer_id: str
    referred_tenant_id: str
    plan_id: str
    eligible: bool
    qualifying_payment: Decimal
    referrer_reward: Decimal
    customer_credit: Decimal
    status: ReferralStatus = "pending"

    def __post_init__(self) -> None:
        if not self.referral_id.strip():
            raise ValueError("referral_id is required")
        if not self.referrer_id.strip():
            raise ValueError("referrer_id is required")
        if not self.referred_tenant_id.strip():
            raise ValueError("referred_tenant_id is required")
        if not self.plan_id.strip():
            raise ValueError("plan_id is required")
        if self.qualifying_payment < 0:
            raise ValueError("qualifying_payment cannot be negative")
        if self.referrer_reward < 0:
            raise ValueError("referrer_reward cannot be negative")
        if self.customer_credit < 0:
            raise ValueError("customer_credit cannot be negative")


class EconomicGovernor:
    """Central authority for economic calculation.

    The governor calculates economics only. It does not execute payments,
    approve financial actions, or bypass tenant/authorization controls.
    """

    def calculate_usage_charge(
        self,
        *,
        plan: SubscriptionPlan,
        usage_units: int,
    ) -> Decimal:
        if usage_units < 0:
            raise ValueError("usage_units cannot be negative")

        excess_units = max(
            0,
            usage_units - plan.included_usage_units,
        )

        return _money(
            Decimal(excess_units) * plan.overage_price_per_unit
        )

    def calculate_cost_charge(
        self,
        *,
        actual_cost: Decimal,
        policy: PricingPolicy,
    ) -> Decimal:
        if actual_cost < 0:
            raise ValueError("actual_cost cannot be negative")

        charge = actual_cost * (Decimal("1.00") + policy.markup_rate)
        charge = max(charge, policy.minimum_charge)

        return _money(charge)

    def calculate_referral(
        self,
        *,
        referral_id: str,
        referrer_id: str | None,
        referred_tenant_id: str,
        plan: SubscriptionPlan,
        subscription_level: int,
        qualifying_payment: Decimal,
        policy: ReferralPolicy,
    ) -> ReferralRecord:
        if not referral_id.strip():
            raise ValueError("referral_id is required")
        if not referred_tenant_id.strip():
            raise ValueError("referred_tenant_id is required")
        if subscription_level < 1:
            raise ValueError("subscription_level must be positive")
        if qualifying_payment < 0:
            raise ValueError("qualifying_payment cannot be negative")

        eligible = (
            referrer_id is not None
            and bool(referrer_id.strip())
            and subscription_level >= policy.minimum_subscription_level
            and qualifying_payment > 0
        )

        if not eligible:
            return ReferralRecord(
                referral_id=referral_id,
                referrer_id=referrer_id or "",
                referred_tenant_id=referred_tenant_id,
                plan_id=plan.plan_id,
                eligible=False,
                qualifying_payment=_money(qualifying_payment),
                referrer_reward=Decimal("0.00"),
                customer_credit=Decimal("0.00"),
                status="rejected",
            )

        payment = _money(qualifying_payment)

        return ReferralRecord(
            referral_id=referral_id,
            referrer_id=referrer_id,
            referred_tenant_id=referred_tenant_id,
            plan_id=plan.plan_id,
            eligible=True,
            qualifying_payment=payment,
            referrer_reward=_money(payment * policy.referrer_rate),
            customer_credit=_money(payment * policy.customer_rate),
            status="confirmed",
        )

    def create_billing_record(
        self,
        *,
        billing_id: str,
        tenant_id: str,
        plan: SubscriptionPlan,
        usage_units: int = 0,
        referral_credit: Decimal = Decimal("0.00"),
    ) -> BillingRecord:
        if referral_credit < 0:
            raise ValueError("referral_credit cannot be negative")

        usage_amount = self.calculate_usage_charge(
            plan=plan,
            usage_units=usage_units,
        )

        subscription_amount = _money(plan.monthly_price)
        credit = _money(referral_credit)

        total_due = max(
            Decimal("0.00"),
            subscription_amount + usage_amount - credit,
        )

        return BillingRecord(
            billing_id=billing_id,
            tenant_id=tenant_id,
            plan_id=plan.plan_id,
            subscription_amount=subscription_amount,
            usage_amount=usage_amount,
            referral_credit=credit,
            total_due=_money(total_due),
            currency=plan.currency,
            status="draft",
        )


__all__ = [
    "BillingRecord",
    "BillingStatus",
    "EconomicGovernor",
    "PricingPolicy",
    "ReferralPolicy",
    "ReferralRecord",
    "ReferralStatus",
    "SubscriptionPlan",
]
