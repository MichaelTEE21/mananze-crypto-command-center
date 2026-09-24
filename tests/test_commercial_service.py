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

def test_reconcile_provider_usage_applies_pricing_and_is_idempotent():
    from mananze_os.provider_observability import ProviderUsageLedger

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
    )

    pricing = PricingPolicy(
        policy_id="standard-margin",
        markup_rate=Decimal("0.75"),
    )

    usage_ledger = ProviderUsageLedger()
    usage_record = usage_ledger.record(
        provider_id="provider-openai",
        tool_id="ai-completion",
        tenant_id="tenant-001",
        execution_id="exec-001",
        success=True,
        latency_ms=120.0,
        usage={"input_tokens": 100, "output_tokens": 50},
        cost=0.20,
        cost_currency="ZAR",
    )

    service = CommercialService()

    first = service.reconcile_provider_usage(
        usage_record=usage_record,
        plan=plan,
        pricing_policy=pricing,
        billing_period="2026-09",
    )

    second = service.reconcile_provider_usage(
        usage_record=usage_record,
        plan=plan,
        pricing_policy=pricing,
        billing_period="2026-09",
    )

    assert first.reconciled is True
    assert first.actual_cost == Decimal("0.20")
    assert first.client_charge == Decimal("0.35")

    assert second.reconciled is False
    assert second.client_charge == Decimal("0.35")


def test_reconcile_provider_usage_rejects_failed_execution():
    from mananze_os.provider_observability import ProviderUsageLedger

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
    )

    pricing = PricingPolicy(
        policy_id="standard-margin",
        markup_rate=Decimal("0.75"),
    )

    usage_ledger = ProviderUsageLedger()
    usage_record = usage_ledger.record(
        provider_id="provider-openai",
        tool_id="ai-completion",
        tenant_id="tenant-001",
        execution_id="exec-failed",
        success=False,
        latency_ms=120.0,
        usage=None,
        cost=0.0,
        cost_currency="ZAR",
    )

    service = CommercialService()

    try:
        service.reconcile_provider_usage(
            usage_record=usage_record,
            plan=plan,
            pricing_policy=pricing,
            billing_period="2026-09",
        )
    except ValueError as exc:
        assert "failed provider executions" in str(exc)
    else:
        raise AssertionError("failed execution was incorrectly billable")


def test_reconcile_provider_usage_rejects_currency_mismatch():
    from mananze_os.provider_observability import ProviderUsageLedger

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
    )

    pricing = PricingPolicy(
        policy_id="standard-margin",
        markup_rate=Decimal("0.75"),
    )

    usage_ledger = ProviderUsageLedger()
    usage_record = usage_ledger.record(
        provider_id="provider-openai",
        tool_id="ai-completion",
        tenant_id="tenant-001",
        execution_id="exec-usd",
        success=True,
        latency_ms=120.0,
        usage={"tokens": 100},
        cost=0.20,
        cost_currency="USD",
    )

    service = CommercialService()

    try:
        service.reconcile_provider_usage(
            usage_record=usage_record,
            plan=plan,
            pricing_policy=pricing,
            billing_period="2026-09",
        )
    except ValueError as exc:
        assert "currency" in str(exc).lower()
    else:
        raise AssertionError("currency mismatch was incorrectly accepted")

def test_reconcile_provider_usage_persists_to_sqlite_and_survives_restart(tmp_path):
    from mananze_os.provider_observability import ProviderUsageLedger
    from mananze_os.sqlite_commercial_store import SQLiteCommercialStore

    db_path = tmp_path / "commercial.db"

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
    )

    pricing = PricingPolicy(
        policy_id="standard-margin",
        markup_rate=Decimal("0.75"),
    )

    usage_ledger = ProviderUsageLedger()
    usage_record = usage_ledger.record(
        provider_id="provider-openai",
        tool_id="ai-completion",
        tenant_id="tenant-001",
        execution_id="exec-durable-001",
        success=True,
        latency_ms=100.0,
        usage={"input_tokens": 100},
        cost=Decimal("200.00"),
        cost_currency="ZAR",
    )

    store = SQLiteCommercialStore(db_path)
    service = CommercialService(store=store)

    first = service.reconcile_provider_usage(
        usage_record=usage_record,
        plan=plan,
        pricing_policy=pricing,
        billing_period="2026-09",
    )

    assert first.reconciled is True
    assert first.client_charge == Decimal("350.00")

    persisted = store.get_provider_charge("exec-durable-001")

    assert persisted["execution_id"] == "exec-durable-001"
    assert persisted["tenant_id"] == "tenant-001"
    assert persisted["actual_cost"] == "200.00"
    assert persisted["client_charge"] == "350.00"
    assert persisted["billing_period"] == "2026-09"

    # Simulate a new service/store instance after restart.
    restarted_store = SQLiteCommercialStore(db_path)
    restarted_service = CommercialService(store=restarted_store)

    second = restarted_service.reconcile_provider_usage(
        usage_record=usage_record,
        plan=plan,
        pricing_policy=pricing,
        billing_period="2026-09",
    )

    assert second.reconciled is False

    charges = restarted_store.list_provider_charges(
        tenant_id="tenant-001"
    )

    assert len(charges) == 1
    assert charges[0]["execution_id"] == "exec-durable-001"


def test_reconcile_provider_usage_is_tenant_scoped(tmp_path):
    from mananze_os.provider_observability import ProviderUsageLedger
    from mananze_os.sqlite_commercial_store import SQLiteCommercialStore

    db_path = tmp_path / "commercial.db"

    plan = SubscriptionPlan(
        plan_id="level-2",
        name="Level 2",
        monthly_price=Decimal("1500.00"),
        currency="ZAR",
    )

    pricing = PricingPolicy(
        policy_id="standard-margin",
        markup_rate=Decimal("0.75"),
    )

    usage_ledger = ProviderUsageLedger()

    tenant_a = usage_ledger.record(
        provider_id="provider-a",
        tool_id="tool-a",
        tenant_id="tenant-a",
        execution_id="exec-a",
        success=True,
        latency_ms=50.0,
        usage={"units": 1},
        cost=Decimal("10.00"),
        cost_currency="ZAR",
    )

    tenant_b = usage_ledger.record(
        provider_id="provider-b",
        tool_id="tool-b",
        tenant_id="tenant-b",
        execution_id="exec-b",
        success=True,
        latency_ms=50.0,
        usage={"units": 1},
        cost=Decimal("20.00"),
        cost_currency="ZAR",
    )

    store = SQLiteCommercialStore(db_path)
    service = CommercialService(store=store)

    service.reconcile_provider_usage(
        usage_record=tenant_a,
        plan=plan,
        pricing_policy=pricing,
        billing_period="2026-09",
    )

    assert len(store.list_provider_charges(tenant_id="tenant-a")) == 1
    assert len(store.list_provider_charges(tenant_id="tenant-b")) == 0

    # Tenant B is reconciled independently.
    service.reconcile_provider_usage(
        usage_record=tenant_b,
        plan=plan,
        pricing_policy=pricing,
        billing_period="2026-09",
    )

    assert len(store.list_provider_charges(tenant_id="tenant-a")) == 1
    assert len(store.list_provider_charges(tenant_id="tenant-b")) == 1
