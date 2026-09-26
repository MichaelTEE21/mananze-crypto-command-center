import pytest

from mananze_os.fulfilment_strategy import FulfilmentStrategy
from mananze_os.job import Job
from mananze_os.job_fulfilment import resolve_job_fulfilment


def make_job(*, tenant_id="tenant-1"):
    return Job(
        job_id="job-1",
        tenant_id=tenant_id,
        quote_id="quote-1",
        customer_reference="Customer A",
    )


def make_strategy(
    *,
    strategy_type="inventory_first",
    tenant_id="tenant-1",
    confirmation_status="confirmed",
):
    return FulfilmentStrategy(
        strategy_id="strategy-1",
        tenant_id=tenant_id,
        strategy_type=strategy_type,
        name="Business fulfilment strategy",
        confirmation_status=confirmation_status,
        evidence_ids=("strategy-evidence-1",),
    )


@pytest.mark.parametrize(
    ("strategy_type", "expected"),
    [
        ("inventory_first", "inventory"),
        ("procurement_after_payment", "procurement"),
        ("procurement_before_payment", "procurement"),
        ("make_to_order", "make_to_order"),
        ("service_delivery", "service_delivery"),
        ("hybrid", "hybrid"),
        ("custom", "custom"),
    ],
)
def test_confirmed_strategy_resolves_to_fulfilment_path(
    strategy_type,
    expected,
):
    result = resolve_job_fulfilment(
        job=make_job(),
        strategy=make_strategy(strategy_type=strategy_type),
    )

    assert result.job_id == "job-1"
    assert result.tenant_id == "tenant-1"
    assert result.decision == expected
    assert result.strategy_id == "strategy-1"


def test_strategy_evidence_is_preserved():
    result = resolve_job_fulfilment(
        job=make_job(),
        strategy=make_strategy(),
    )

    assert result.evidence_ids == ("strategy-evidence-1",)


def test_tenant_mismatch_is_rejected():
    with pytest.raises(ValueError, match="tenant"):
        resolve_job_fulfilment(
            job=make_job(tenant_id="tenant-1"),
            strategy=make_strategy(tenant_id="tenant-2"),
        )


def test_unconfirmed_strategy_is_rejected():
    with pytest.raises(ValueError, match="not confirmed"):
        resolve_job_fulfilment(
            job=make_job(),
            strategy=make_strategy(
                confirmation_status="unconfirmed",
            ),
        )


def test_partially_confirmed_strategy_is_rejected():
    with pytest.raises(ValueError, match="not confirmed"):
        resolve_job_fulfilment(
            job=make_job(),
            strategy=make_strategy(
                confirmation_status="partially_confirmed",
            ),
        )


def test_decision_does_not_change_job_status():
    job = make_job()

    result = resolve_job_fulfilment(
        job=job,
        strategy=make_strategy(),
    )

    assert job.status == "created"
    assert result.decision == "inventory"


def test_decision_does_not_execute_fulfilment():
    result = resolve_job_fulfilment(
        job=make_job(),
        strategy=make_strategy(
            strategy_type="procurement_after_payment",
        ),
    )

    assert result.decision == "procurement"


def test_strategy_identity_is_preserved():
    strategy = make_strategy()

    result = resolve_job_fulfilment(
        job=make_job(),
        strategy=strategy,
    )

    assert result.strategy_id == strategy.strategy_id


def test_job_identity_is_preserved():
    result = resolve_job_fulfilment(
        job=make_job(),
        strategy=make_strategy(),
    )

    assert result.job_id == "job-1"


def test_tenant_identity_is_preserved():
    result = resolve_job_fulfilment(
        job=make_job(),
        strategy=make_strategy(),
    )

    assert result.tenant_id == "tenant-1"
