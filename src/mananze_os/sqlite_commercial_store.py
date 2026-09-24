"""SQLite-backed durable commercial persistence for Mananze OS.

Persistence for subscriptions, billing entries, and referral ledger entries.
This module stores commercial state; it does not move money or grant
financial authority.
"""

from __future__ import annotations

import sqlite3
from decimal import Decimal
from pathlib import Path
from threading import RLock

from mananze_os.commercial_ledger import (
    BillingLedgerEntry,
    CommercialLedger,
    ReferralLedgerEntry,
    SubscriptionRecord,
)


class SQLiteCommercialStore:
    """Durable commercial store backed by SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = RLock()

        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=FULL;

                CREATE TABLE IF NOT EXISTS commercial_subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    subscription_level INTEGER NOT NULL,
                    monthly_price TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS commercial_billing (
                    billing_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    billing_period TEXT NOT NULL,
                    amount_due TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    payment_id TEXT UNIQUE,
                    status TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS commercial_referrals (
                    referral_id TEXT PRIMARY KEY,
                    qualifying_payment_id TEXT NOT NULL UNIQUE,
                    referrer_id TEXT NOT NULL,
                    referred_tenant_id TEXT NOT NULL,
                    reward_amount TEXT NOT NULL,
                    customer_credit TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_commercial_subscriptions_tenant
                    ON commercial_subscriptions(tenant_id);

                CREATE INDEX IF NOT EXISTS idx_commercial_billing_tenant
                    ON commercial_billing(tenant_id, billing_period);

                CREATE INDEX IF NOT EXISTS idx_commercial_referrals_tenant
                    ON commercial_referrals(referred_tenant_id);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.path,
            timeout=30.0,
            isolation_level="DEFERRED",
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    @staticmethod
    def _row_to_subscription(row: sqlite3.Row) -> SubscriptionRecord:
        return SubscriptionRecord(
            subscription_id=row["subscription_id"],
            tenant_id=row["tenant_id"],
            plan_id=row["plan_id"],
            subscription_level=row["subscription_level"],
            monthly_price=Decimal(row["monthly_price"]),
            currency=row["currency"],
            status=row["status"],
        )

    @staticmethod
    def _row_to_billing(row: sqlite3.Row) -> BillingLedgerEntry:
        return BillingLedgerEntry(
            billing_id=row["billing_id"],
            tenant_id=row["tenant_id"],
            billing_period=row["billing_period"],
            amount_due=Decimal(row["amount_due"]),
            currency=row["currency"],
            payment_id=row["payment_id"],
            status=row["status"],
        )

    @staticmethod
    def _row_to_referral(row: sqlite3.Row) -> ReferralLedgerEntry:
        return ReferralLedgerEntry(
            referral_id=row["referral_id"],
            qualifying_payment_id=row["qualifying_payment_id"],
            referrer_id=row["referrer_id"],
            referred_tenant_id=row["referred_tenant_id"],
            reward_amount=Decimal(row["reward_amount"]),
            customer_credit=Decimal(row["customer_credit"]),
            currency=row["currency"],
            status=row["status"],
        )

    def add_subscription(
        self,
        subscription: SubscriptionRecord,
    ) -> SubscriptionRecord:
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO commercial_subscriptions (
                        subscription_id,
                        tenant_id,
                        plan_id,
                        subscription_level,
                        monthly_price,
                        currency,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscription.subscription_id,
                        subscription.tenant_id,
                        subscription.plan_id,
                        subscription.subscription_level,
                        str(subscription.monthly_price),
                        subscription.currency,
                        subscription.status,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if "UNIQUE" in str(exc).upper() or "PRIMARY KEY" in str(exc).upper():
                    raise ValueError(
                        f"subscription already exists: {subscription.subscription_id}"
                    ) from exc
                raise

        return subscription

    def get_subscription(self, subscription_id: str) -> SubscriptionRecord:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM commercial_subscriptions
                WHERE subscription_id = ?
                """,
                (subscription_id,),
            ).fetchone()

        if row is None:
            raise KeyError(
                f"unknown subscription: {subscription_id}"
            )

        return self._row_to_subscription(row)

    def list_subscriptions(
        self,
        tenant_id: str | None = None,
    ) -> tuple[SubscriptionRecord, ...]:
        with self._lock, self._connect() as conn:
            if tenant_id is None:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM commercial_subscriptions
                    ORDER BY subscription_id
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM commercial_subscriptions
                    WHERE tenant_id = ?
                    ORDER BY subscription_id
                    """,
                    (tenant_id,),
                ).fetchall()

        return tuple(
            self._row_to_subscription(row)
            for row in rows
        )

    def add_billing_entry(
        self,
        entry: BillingLedgerEntry,
    ) -> BillingLedgerEntry:
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO commercial_billing (
                        billing_id,
                        tenant_id,
                        billing_period,
                        amount_due,
                        currency,
                        payment_id,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.billing_id,
                        entry.tenant_id,
                        entry.billing_period,
                        str(entry.amount_due),
                        entry.currency,
                        entry.payment_id,
                        entry.status,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    f"billing entry already exists: {entry.billing_id}"
                ) from exc

        return entry

    def get_billing_entry(
        self,
        billing_id: str,
    ) -> BillingLedgerEntry:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM commercial_billing
                WHERE billing_id = ?
                """,
                (billing_id,),
            ).fetchone()

        if row is None:
            raise KeyError(
                f"unknown billing entry: {billing_id}"
            )

        return self._row_to_billing(row)

    def confirm_payment(
        self,
        *,
        billing_id: str,
        payment_id: str,
    ) -> BillingLedgerEntry:
        if not payment_id.strip():
            raise ValueError("payment_id is required")

        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM commercial_billing
                WHERE billing_id = ?
                """,
                (billing_id,),
            ).fetchone()

            if row is None:
                raise KeyError(
                    f"unknown billing entry: {billing_id}"
                )

            entry = self._row_to_billing(row)

            if entry.status == "paid":
                if entry.payment_id != payment_id:
                    raise ValueError(
                        "billing entry is already paid by another payment"
                    )
                return entry

            existing_payment = conn.execute(
                """
                SELECT billing_id
                FROM commercial_billing
                WHERE payment_id = ?
                """,
                (payment_id,),
            ).fetchone()

            if existing_payment is not None:
                raise ValueError(
                    f"payment already processed: {payment_id}"
                )

            cursor = conn.execute(
                """
                UPDATE commercial_billing
                SET payment_id = ?,
                    status = 'paid'
                WHERE billing_id = ?
                  AND status != 'paid'
                """,
                (
                    payment_id,
                    billing_id,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "billing payment confirmation was not durably applied"
                )

            updated = conn.execute(
                """
                SELECT *
                FROM commercial_billing
                WHERE billing_id = ?
                """,
                (billing_id,),
            ).fetchone()

        return self._row_to_billing(updated)

    def list_billing_entries(
        self,
        tenant_id: str | None = None,
    ) -> tuple[BillingLedgerEntry, ...]:
        with self._lock, self._connect() as conn:
            if tenant_id is None:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM commercial_billing
                    ORDER BY billing_period, billing_id
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM commercial_billing
                    WHERE tenant_id = ?
                    ORDER BY billing_period, billing_id
                    """,
                    (tenant_id,),
                ).fetchall()

        return tuple(
            self._row_to_billing(row)
            for row in rows
        )

    def add_referral(
        self,
        referral: ReferralLedgerEntry,
    ) -> ReferralLedgerEntry:
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO commercial_referrals (
                        referral_id,
                        qualifying_payment_id,
                        referrer_id,
                        referred_tenant_id,
                        reward_amount,
                        customer_credit,
                        currency,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        referral.referral_id,
                        referral.qualifying_payment_id,
                        referral.referrer_id,
                        referral.referred_tenant_id,
                        str(referral.reward_amount),
                        str(referral.customer_credit),
                        referral.currency,
                        referral.status,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if "qualifying_payment_id" in str(exc):
                    raise ValueError(
                        "qualifying payment already has a referral reward"
                    ) from exc
                raise ValueError(
                    f"referral already exists: {referral.referral_id}"
                ) from exc

        return referral

    def get_referral(
        self,
        referral_id: str,
    ) -> ReferralLedgerEntry:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM commercial_referrals
                WHERE referral_id = ?
                """,
                (referral_id,),
            ).fetchone()

        if row is None:
            raise KeyError(
                f"unknown referral: {referral_id}"
            )

        return self._row_to_referral(row)

    def list_referrals(
        self,
        referred_tenant_id: str | None = None,
    ) -> tuple[ReferralLedgerEntry, ...]:
        with self._lock, self._connect() as conn:
            if referred_tenant_id is None:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM commercial_referrals
                    ORDER BY referral_id
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM commercial_referrals
                    WHERE referred_tenant_id = ?
                    ORDER BY referral_id
                    """,
                    (referred_tenant_id,),
                ).fetchall()

        return tuple(
            self._row_to_referral(row)
            for row in rows
        )


__all__ = ["SQLiteCommercialStore"]
