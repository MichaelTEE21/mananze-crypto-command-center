"""Commercial orchestration boundary for Mananze OS.

Coordinates economic calculation, commercial ledger recording, and
durable commercial persistence. It does not move money or grant authority.
"""

from dataclasses import dataclass
from decimal import Decimal

from mananze_os.commercial_ledger import (
    BillingLedgerEntry,
    CommercialLedger,
    ReferralLedgerEntry,
    SubscriptionRecord,
)
from mananze_os.economic_governor import (
    BillingRecord,
    EconomicGovernor,
    PricingPolicy,
    ReferralPolicy,
    ReferralRecord,
    SubscriptionPlan,
)
from mananze_os.sqlite_commercial_store import SQLiteCommercialStore


@dataclass(frozen=True)
class CommercialExecution:
    """Result of one commercial orchestration operation."""

    billing: BillingRecord
    billing_entry: BillingLedgerEntry
    provider_charge: Decimal | None
    referral: ReferralRecord | None
    referral_entry: ReferralLedgerEntry | None


class CommercialService:
    """Coordinate economic calculation, ledger state, and persistence."""

    def __init__(
        self,
        *,
        economic_governor: EconomicGovernor | None = None,
        ledger: CommercialLedger | None = None,
        store: SQLiteCommercialStore | None = None,
    ) -> None:
        self.economic_governor = (
            economic_governor or EconomicGovernor()
        )
        self.ledger = ledger or CommercialLedger()
        self.store = store

    def create_subscription(
        self,
        *,
        subscription_id: str,
        tenant_id: str,
        plan: SubscriptionPlan,
        subscription_level: int,
    ) -> SubscriptionRecord:
        record = SubscriptionRecord(
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            plan_id=plan.plan_id,
            subscription_level=subscription_level,
            monthly_price=plan.monthly_price,
            currency=plan.currency,
            status="pending",
        )

        self.ledger.add_subscription(record)

        if self.store is not None:
            self.store.add_subscription(record)

        return record

    def create_billing(
        self,
        *,
        billing_id: str,
        tenant_id: str,
        plan: SubscriptionPlan,
        billing_period: str,
        usage_units: int = 0,
        referral_credit: Decimal = Decimal("0.00"),
        actual_provider_cost: Decimal | None = None,
        pricing_policy: PricingPolicy | None = None,
    ) -> CommercialExecution:
        billing = self.economic_governor.create_billing_record(
            billing_id=billing_id,
            tenant_id=tenant_id,
            plan=plan,
            usage_units=usage_units,
            referral_credit=referral_credit,
        )

        provider_charge = None

        if actual_provider_cost is not None:
            if pricing_policy is None:
                raise ValueError(
                    "pricing_policy is required when actual_provider_cost is supplied"
                )

            provider_charge = (
                self.economic_governor.calculate_cost_charge(
                    actual_cost=actual_provider_cost,
                    policy=pricing_policy,
                )
            )

        billing_entry = BillingLedgerEntry(
            billing_id=billing.billing_id,
            tenant_id=billing.tenant_id,
            billing_period=billing_period,
            amount_due=billing.total_due,
            currency=billing.currency,
            status="pending",
        )

        self.ledger.add_billing_entry(billing_entry)

        if self.store is not None:
            self.store.add_billing_entry(billing_entry)

        return CommercialExecution(
            billing=billing,
            billing_entry=billing_entry,
            provider_charge=provider_charge,
            referral=None,
            referral_entry=None,
        )

    def create_referral(
        self,
        *,
        referral_id: str,
        referrer_id: str | None,
        referred_tenant_id: str,
        plan: SubscriptionPlan,
        subscription_level: int,
        qualifying_payment: Decimal,
        policy: ReferralPolicy,
        qualifying_payment_id: str,
    ) -> tuple[ReferralRecord, ReferralLedgerEntry | None]:
        referral = self.economic_governor.calculate_referral(
            referral_id=referral_id,
            referrer_id=referrer_id,
            referred_tenant_id=referred_tenant_id,
            plan=plan,
            subscription_level=subscription_level,
            qualifying_payment=qualifying_payment,
            policy=policy,
        )

        if not referral.eligible:
            return referral, None

        entry = ReferralLedgerEntry(
            referral_id=referral.referral_id,
            qualifying_payment_id=qualifying_payment_id,
            referrer_id=referral.referrer_id,
            referred_tenant_id=referral.referred_tenant_id,
            reward_amount=referral.referrer_reward,
            customer_credit=referral.customer_credit,
            currency=plan.currency,
            status="pending",
        )

        self.ledger.add_referral(entry)

        if self.store is not None:
            self.store.add_referral(entry)

        return referral, entry


__all__ = [
    "CommercialExecution",
    "CommercialService",
]
