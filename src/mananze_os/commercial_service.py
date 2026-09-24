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


@dataclass(frozen=True)
class ProviderChargeReconciliation:
    """Result of reconciling one successful provider execution."""

    execution_id: str
    provider_id: str
    tool_id: str
    tenant_id: str
    actual_cost: Decimal
    cost_currency: str
    client_charge: Decimal
    pricing_policy_id: str
    billing_period: str
    reconciled: bool


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
        self._reconciled_provider_executions: set[str] = set()

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


    def aggregate_billing_period(
        self,
        *,
        billing_id: str,
        tenant_id: str,
        plan: SubscriptionPlan,
        billing_period: str,
        usage_units: int = 0,
        referral_credit: Decimal = Decimal("0.00"),
    ) -> CommercialExecution:
        """Create one durable billing entry for a billing period.

        The final client amount combines:
        subscription + usage + reconciled provider charges
        - referral credit.

        Provider charges are already priced by the Economic Governor
        during provider reconciliation. This method aggregates those
        durable client charges into the billing period.
        """
        if self.store is None:
            raise ValueError(
                "SQLiteCommercialStore is required for billing-period aggregation"
            )

        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not billing_period.strip():
            raise ValueError("billing_period is required")

        try:
            existing = self.store.get_billing_entry(billing_id)
        except KeyError:
            existing = None

        if existing is not None:
            if existing.tenant_id != tenant_id:
                raise PermissionError(
                    "billing entry belongs to another tenant"
                )

            if existing.billing_period != billing_period:
                raise ValueError(
                    "existing billing entry belongs to another billing period"
                )

            if existing.currency != plan.currency:
                raise ValueError(
                    "existing billing entry currency does not match plan currency"
                )

            existing_amount = Decimal(str(existing.amount_due))

            provider_total = Decimal("0.00")

            for charge in self.store.list_provider_charges(
                tenant_id=tenant_id
            ):
                if charge["billing_period"] != billing_period:
                    continue

                if charge["cost_currency"] != plan.currency:
                    raise ValueError(
                        "provider charge currency does not match plan currency"
                    )

                provider_total += Decimal(str(charge["client_charge"]))

            provider_total = provider_total.quantize(Decimal("0.01"))

            billing = self.economic_governor.create_billing_record(
                billing_id=billing_id,
                tenant_id=tenant_id,
                plan=plan,
                usage_units=usage_units,
                referral_credit=referral_credit,
            )

            billing = billing.__class__(
                billing_id=billing.billing_id,
                tenant_id=billing.tenant_id,
                plan_id=billing.plan_id,
                subscription_amount=billing.subscription_amount,
                usage_amount=billing.usage_amount,
                referral_credit=billing.referral_credit,
                total_due=existing_amount,
                currency=billing.currency,
                status=billing.status,
            )

            billing_entry = BillingLedgerEntry(
                billing_id=existing.billing_id,
                tenant_id=existing.tenant_id,
                billing_period=existing.billing_period,
                amount_due=existing_amount,
                currency=existing.currency,
                status=existing.status,
            )

            return CommercialExecution(
                billing=billing,
                billing_entry=billing_entry,
                provider_charge=provider_total,
                referral=None,
                referral_entry=None,
            )

        base_billing = self.economic_governor.create_billing_record(
            billing_id=billing_id,
            tenant_id=tenant_id,
            plan=plan,
            usage_units=usage_units,
            referral_credit=referral_credit,
        )

        provider_total = Decimal("0.00")

        for charge in self.store.list_provider_charges(
            tenant_id=tenant_id
        ):
            if charge["billing_period"] != billing_period:
                continue

            if charge["cost_currency"] != plan.currency:
                raise ValueError(
                    "provider charge currency does not match plan currency"
                )

            provider_total += Decimal(str(charge["client_charge"]))

        provider_total = provider_total.quantize(Decimal("0.01"))

        final_total = (
            base_billing.total_due + provider_total
        ).quantize(Decimal("0.01"))

        billing = base_billing.__class__(
            billing_id=billing_id,
            tenant_id=base_billing.tenant_id,
            plan_id=base_billing.plan_id,
            subscription_amount=base_billing.subscription_amount,
            usage_amount=base_billing.usage_amount,
            referral_credit=base_billing.referral_credit,
            total_due=final_total,
            currency=base_billing.currency,
            status=base_billing.status,
        )

        billing_entry = BillingLedgerEntry(
            billing_id=billing_id,
            tenant_id=tenant_id,
            billing_period=billing_period,
            amount_due=final_total,
            currency=plan.currency,
            status="pending",
        )

        self.ledger.add_billing_entry(billing_entry)
        self.store.add_billing_entry(billing_entry)

        return CommercialExecution(
            billing=billing,
            billing_entry=billing_entry,
            provider_charge=provider_total,
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


    def reconcile_provider_usage(
        self,
        *,
        usage_record,
        plan: SubscriptionPlan,
        pricing_policy: PricingPolicy,
        billing_period: str,
    ) -> ProviderChargeReconciliation:
        """Convert one successful provider observation into a durable charge.

        ProviderUsageLedger remains an observation layer. This method is the
        commercial boundary that applies Economic Governor pricing and records
        the resulting client charge.

        Provider cost and client charge remain separate values.
        """

        if not billing_period.strip():
            raise ValueError("billing_period is required")

        if not usage_record.success:
            raise ValueError(
                "failed provider executions cannot become client charges"
            )

        if usage_record.cost < 0:
            raise ValueError("provider cost cannot be negative")

        if usage_record.cost_currency != plan.currency:
            raise ValueError(
                "provider cost currency must match plan currency; "
                "FX normalization is required before reconciliation"
            )

        if usage_record.tenant_id.strip() == "":
            raise ValueError("tenant_id is required")

        client_charge = self.economic_governor.calculate_cost_charge(
            actual_cost=Decimal(str(usage_record.cost)),
            policy=pricing_policy,
        )

        if self.store is not None:
            reconciled = self.store.add_provider_charge(
                execution_id=usage_record.execution_id,
                provider_id=usage_record.provider_id,
                tool_id=usage_record.tool_id,
                tenant_id=usage_record.tenant_id,
                actual_cost=Decimal(str(usage_record.cost)),
                cost_currency=usage_record.cost_currency,
                client_charge=client_charge,
                pricing_policy_id=pricing_policy.policy_id,
                billing_period=billing_period,
            )
        else:
            if usage_record.execution_id in self._reconciled_provider_executions:
                reconciled = False
            else:
                self._reconciled_provider_executions.add(
                    usage_record.execution_id
                )
                reconciled = True

        return ProviderChargeReconciliation(
            execution_id=usage_record.execution_id,
            provider_id=usage_record.provider_id,
            tool_id=usage_record.tool_id,
            tenant_id=usage_record.tenant_id,
            actual_cost=Decimal(str(usage_record.cost)),
            cost_currency=usage_record.cost_currency,
            client_charge=client_charge,
            pricing_policy_id=pricing_policy.policy_id,
            billing_period=billing_period,
            reconciled=reconciled,
        )


__all__ = [
    "CommercialExecution",
    "CommercialService",
    "ProviderChargeReconciliation",
]
