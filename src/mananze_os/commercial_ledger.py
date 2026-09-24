"""Durable commercial ledgers for Mananze OS.

Tracks subscriptions, billing records, and referral rewards.
This module records economic state; it does not move money or grant
financial authority.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


SubscriptionStatus = Literal[
    "pending",
    "active",
    "past_due",
    "cancelled",
    "expired",
]

LedgerStatus = Literal[
    "pending",
    "confirmed",
    "paid",
    "cancelled",
    "refunded",
]

CommissionStatus = Literal[
    "pending",
    "approved",
    "paid",
    "reversed",
]


@dataclass(frozen=True)
class SubscriptionRecord:
    subscription_id: str
    tenant_id: str
    plan_id: str
    subscription_level: int
    monthly_price: Decimal
    currency: str
    status: SubscriptionStatus = "pending"

    def __post_init__(self) -> None:
        if not self.subscription_id.strip():
            raise ValueError("subscription_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.plan_id.strip():
            raise ValueError("plan_id is required")
        if self.subscription_level < 1:
            raise ValueError("subscription_level must be positive")
        if self.monthly_price < 0:
            raise ValueError("monthly_price cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")


@dataclass(frozen=True)
class BillingLedgerEntry:
    billing_id: str
    tenant_id: str
    billing_period: str
    amount_due: Decimal
    currency: str
    payment_id: str | None = None
    status: LedgerStatus = "pending"

    def __post_init__(self) -> None:
        if not self.billing_id.strip():
            raise ValueError("billing_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.billing_period.strip():
            raise ValueError("billing_period is required")
        if self.amount_due < 0:
            raise ValueError("amount_due cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")


@dataclass(frozen=True)
class ReferralLedgerEntry:
    referral_id: str
    qualifying_payment_id: str
    referrer_id: str
    referred_tenant_id: str
    reward_amount: Decimal
    customer_credit: Decimal
    currency: str
    status: CommissionStatus = "pending"

    def __post_init__(self) -> None:
        if not self.referral_id.strip():
            raise ValueError("referral_id is required")
        if not self.qualifying_payment_id.strip():
            raise ValueError("qualifying_payment_id is required")
        if not self.referrer_id.strip():
            raise ValueError("referrer_id is required")
        if not self.referred_tenant_id.strip():
            raise ValueError("referred_tenant_id is required")
        if self.reward_amount < 0:
            raise ValueError("reward_amount cannot be negative")
        if self.customer_credit < 0:
            raise ValueError("customer_credit cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")


class CommercialLedger:
    """In-memory commercial ledger with idempotent payment/referral handling.

    Persistence will be added through the existing durable storage layer.
    This first version establishes the domain contract and idempotency rules.
    """

    def __init__(self) -> None:
        self._subscriptions: dict[str, SubscriptionRecord] = {}
        self._billing: dict[str, BillingLedgerEntry] = {}
        self._referrals: dict[str, ReferralLedgerEntry] = {}
        self._processed_payment_ids: set[str] = set()

    def add_subscription(
        self,
        subscription: SubscriptionRecord,
    ) -> SubscriptionRecord:
        if subscription.subscription_id in self._subscriptions:
            raise ValueError(
                f"subscription already exists: "
                f"{subscription.subscription_id}"
            )

        self._subscriptions[
            subscription.subscription_id
        ] = subscription

        return subscription

    def get_subscription(
        self,
        subscription_id: str,
    ) -> SubscriptionRecord:
        try:
            return self._subscriptions[subscription_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown subscription: {subscription_id}"
            ) from exc

    def add_billing_entry(
        self,
        entry: BillingLedgerEntry,
    ) -> BillingLedgerEntry:
        if entry.billing_id in self._billing:
            raise ValueError(
                f"billing entry already exists: {entry.billing_id}"
            )

        self._billing[entry.billing_id] = entry
        return entry

    def get_billing_entry(
        self,
        billing_id: str,
    ) -> BillingLedgerEntry:
        try:
            return self._billing[billing_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown billing entry: {billing_id}"
            ) from exc

    def confirm_payment(
        self,
        *,
        billing_id: str,
        payment_id: str,
    ) -> BillingLedgerEntry:
        if not payment_id.strip():
            raise ValueError("payment_id is required")

        entry = self.get_billing_entry(billing_id)

        if entry.status == "paid":
            if entry.payment_id != payment_id:
                raise ValueError(
                    "billing entry is already paid by another payment"
                )
            return entry

        if payment_id in self._processed_payment_ids:
            raise ValueError(
                f"payment already processed: {payment_id}"
            )

        confirmed = BillingLedgerEntry(
            billing_id=entry.billing_id,
            tenant_id=entry.tenant_id,
            billing_period=entry.billing_period,
            amount_due=entry.amount_due,
            currency=entry.currency,
            payment_id=payment_id,
            status="paid",
        )

        self._billing[billing_id] = confirmed
        self._processed_payment_ids.add(payment_id)

        return confirmed

    def add_referral(
        self,
        referral: ReferralLedgerEntry,
    ) -> ReferralLedgerEntry:
        if referral.referral_id in self._referrals:
            raise ValueError(
                f"referral already exists: {referral.referral_id}"
            )

        if referral.qualifying_payment_id in {
            item.qualifying_payment_id
            for item in self._referrals.values()
        }:
            raise ValueError(
                "qualifying payment already has a referral reward"
            )

        self._referrals[referral.referral_id] = referral
        return referral

    def get_referral(
        self,
        referral_id: str,
    ) -> ReferralLedgerEntry:
        try:
            return self._referrals[referral_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown referral: {referral_id}"
            ) from exc

    def subscriptions(self) -> tuple[SubscriptionRecord, ...]:
        return tuple(self._subscriptions.values())

    def billing_entries(self) -> tuple[BillingLedgerEntry, ...]:
        return tuple(self._billing.values())

    def referrals(self) -> tuple[ReferralLedgerEntry, ...]:
        return tuple(self._referrals.values())


__all__ = [
    "BillingLedgerEntry",
    "CommercialLedger",
    "CommissionStatus",
    "LedgerStatus",
    "ReferralLedgerEntry",
    "SubscriptionRecord",
    "SubscriptionStatus",
]
