import pytest

from mananze_os.customer_quote_decision import CustomerQuoteDecision
from mananze_os.fulfilment_strategy import FulfilmentStrategy
from mananze_os.fulfilment_trigger import trigger_job_fulfilment
from mananze_os.job import Job
from mananze_os.payment_confirmation import PaymentConfirmation
from mananze_os.quote import Quote


def make_quote() -> Quote:
    return Quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="customer-1",
        currency="ZAR",
        status="sent",
    )


def make_job() -> Job:
    quote = make_quote()

    decision = CustomerQuoteDecision(
        decision_id="decision-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        decision="accepted",
        decided_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    )

    return Job(
        job_id="job-1",
        tenant_id="tenant-1",
        quote_id=quote.quote_id,
        customer_reference=quote.customer_reference,
        evidence_ids=("quote-1",),
    )


def make_strategy(strategy_type: str) -> FulfilmentStrategy:
    return FulfilmentStrategy(
        strategy_id="strategy-1",
        tenant_id="tenant-1",
        strategy_type=strategy_type,
        name="Business fulfilment strategy",
        confirmation_status="confirmed",
        evidence_ids=("strategy-evidence-1",),
    )


def make_payment(confirmed: bool = True) -> PaymentConfirmation:
    return PaymentConfirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        status="confirmed" if confirmed else "review_required",
        evidence_ids=("pop-1",),
        reference="POP123",
        amount=5000,
        currency="ZAR",
    )


def test_procurement_after_payment_waits_without_payment():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("procurement_after_payment"),
    )

    assert result.triggered is False
    assert result.lifecycle.stage == "fulfilment_pending"


def test_procurement_after_payment_requires_confirmed_payment():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("procurement_after_payment"),
        payment=make_payment(confirmed=False),
    )

    assert result.triggered is False
    assert result.lifecycle.stage == "fulfilment_pending"


def test_procurement_after_payment_proceeds_after_confirmation():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("procurement_after_payment"),
        payment=make_payment(),
    )

    assert result.triggered is True
    assert result.lifecycle.stage == "procurement_pending"
    assert "pop-1" in result.lifecycle.evidence_ids


def test_inventory_first_can_proceed_without_payment():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("inventory_first"),
    )

    assert result.triggered is True
    assert result.lifecycle.stage == "inventory_pending"


def test_procurement_before_payment_can_proceed_without_payment():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("procurement_before_payment"),
    )

    assert result.triggered is True
    assert result.lifecycle.stage == "procurement_pending"


def test_make_to_order_can_proceed():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("make_to_order"),
    )

    assert result.triggered is True
    assert result.lifecycle.stage == "make_to_order_pending"


def test_service_delivery_can_proceed():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("service_delivery"),
    )

    assert result.triggered is True
    assert result.lifecycle.stage == "service_delivery_pending"


def test_hybrid_waits_for_business_specific_workflow():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("hybrid"),
    )

    assert result.triggered is False
    assert result.lifecycle.stage == "fulfilment_pending"


def test_custom_waits_for_business_specific_workflow():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("custom"),
    )

    assert result.triggered is False
    assert result.lifecycle.stage == "fulfilment_pending"


def test_tenant_mismatch_is_rejected():
    strategy = FulfilmentStrategy(
        strategy_id="strategy-1",
        tenant_id="tenant-2",
        strategy_type="inventory_first",
        name="Other tenant strategy",
        confirmation_status="confirmed",
    )

    with pytest.raises(ValueError, match="job tenant"):
        trigger_job_fulfilment(
            job=make_job(),
            strategy=strategy,
        )


def test_payment_tenant_mismatch_is_rejected():
    payment = PaymentConfirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-2",
        quote_id="quote-1",
        status="confirmed",
        evidence_ids=("pop-1",),
    )

    with pytest.raises(ValueError, match="payment tenant"):
        trigger_job_fulfilment(
            job=make_job(),
            strategy=make_strategy("procurement_after_payment"),
            payment=payment,
        )


def test_payment_quote_mismatch_is_rejected():
    payment = PaymentConfirmation(
        confirmation_id="payment-1",
        tenant_id="tenant-1",
        quote_id="quote-2",
        status="confirmed",
        evidence_ids=("pop-1",),
    )

    with pytest.raises(ValueError, match="payment quote"):
        trigger_job_fulfilment(
            job=make_job(),
            strategy=make_strategy("procurement_after_payment"),
            payment=payment,
        )


def test_evidence_is_combined():
    result = trigger_job_fulfilment(
        job=make_job(),
        strategy=make_strategy("procurement_after_payment"),
        payment=make_payment(),
    )

    assert "quote-1" in result.lifecycle.evidence_ids
    assert "strategy-evidence-1" in result.lifecycle.evidence_ids
    assert "pop-1" in result.lifecycle.evidence_ids
