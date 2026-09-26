from datetime import datetime, timezone

import pytest

from mananze_os.customer_quote_decision import CustomerQuoteDecision
from mananze_os.job import create_job_from_accepted_quote
from mananze_os.quote import Quote


def make_quote(
    *,
    status="sent",
    tenant_id="tenant-1",
    quote_id="quote-1",
):
    return Quote(
        quote_id=quote_id,
        tenant_id=tenant_id,
        customer_reference="Customer A",
        currency="ZAR",
        status=status,
    )


def make_decision(
    *,
    decision="accepted",
    tenant_id="tenant-1",
    quote_id="quote-1",
):
    return CustomerQuoteDecision(
        decision_id="decision-1",
        tenant_id=tenant_id,
        quote_id=quote_id,
        decision=decision,
        decided_at=datetime.now(timezone.utc),
        evidence_ids=("decision-evidence-1",),
    )


def test_accepted_quote_creates_job():
    result = create_job_from_accepted_quote(
        job_id="job-1",
        quote=make_quote(),
        customer_decision=make_decision(),
    )

    assert result.job_id == "job-1"
    assert result.tenant_id == "tenant-1"
    assert result.quote_id == "quote-1"
    assert result.customer_reference == "Customer A"
    assert result.status == "created"


def test_quote_and_decision_evidence_are_combined():
    quote = Quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        status="sent",
        evidence_ids=("quote-evidence-1",),
    )

    result = create_job_from_accepted_quote(
        job_id="job-1",
        quote=quote,
        customer_decision=make_decision(),
        evidence_ids=("job-evidence-1",),
    )

    assert result.evidence_ids == (
        "quote-evidence-1",
        "decision-evidence-1",
        "job-evidence-1",
    )


def test_duplicate_evidence_is_deduplicated():
    quote = Quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        status="sent",
        evidence_ids=("shared-evidence",),
    )

    decision = make_decision()
    decision = CustomerQuoteDecision(
        decision_id=decision.decision_id,
        tenant_id=decision.tenant_id,
        quote_id=decision.quote_id,
        decision=decision.decision,
        decided_at=decision.decided_at,
        evidence_ids=("shared-evidence",),
    )

    result = create_job_from_accepted_quote(
        job_id="job-1",
        quote=quote,
        customer_decision=decision,
        evidence_ids=("shared-evidence",),
    )

    assert result.evidence_ids == ("shared-evidence",)


def test_declined_quote_cannot_create_job():
    with pytest.raises(
        ValueError,
        match="accepted quote",
    ):
        create_job_from_accepted_quote(
            job_id="job-1",
            quote=make_quote(),
            customer_decision=make_decision(
                decision="declined",
            ),
        )


def test_quote_must_be_in_send_or_accepted_state():
    with pytest.raises(
        ValueError,
        match="acceptable state",
    ):
        create_job_from_accepted_quote(
            job_id="job-1",
            quote=make_quote(status="draft"),
            customer_decision=make_decision(),
        )


def test_tenant_mismatch_is_rejected():
    with pytest.raises(
        ValueError,
        match="tenant",
    ):
        create_job_from_accepted_quote(
            job_id="job-1",
            quote=make_quote(tenant_id="tenant-1"),
            customer_decision=make_decision(
                tenant_id="tenant-2",
            ),
        )


def test_quote_id_mismatch_is_rejected():
    with pytest.raises(
        ValueError,
        match="quote_id",
    ):
        create_job_from_accepted_quote(
            job_id="job-1",
            quote=make_quote(quote_id="quote-1"),
            customer_decision=make_decision(
                quote_id="quote-2",
            ),
        )


def test_blank_job_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="job_id is required",
    ):
        create_job_from_accepted_quote(
            job_id="",
            quote=make_quote(),
            customer_decision=make_decision(),
        )


def test_job_is_created_without_execution():
    result = create_job_from_accepted_quote(
        job_id="job-1",
        quote=make_quote(),
        customer_decision=make_decision(),
    )

    assert result.status == "created"


def test_customer_reference_is_carried_forward():
    quote = Quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer Specific Reference",
        currency="ZAR",
        status="sent",
    )

    result = create_job_from_accepted_quote(
        job_id="job-1",
        quote=quote,
        customer_decision=make_decision(),
    )

    assert result.customer_reference == "Customer Specific Reference"
