from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.customer_quote_decision import CustomerQuoteDecision


def make_decision(
    *,
    decision="accepted",
    decided_at=None,
    evidence_ids=("whatsapp-message-1",),
):
    return CustomerQuoteDecision(
        decision_id="decision-1",
        tenant_id="tenant-1",
        quote_id="quote-1",
        decision=decision,
        decided_at=(
            decided_at
            if decided_at is not None
            else datetime.now(timezone.utc)
        ),
        evidence_ids=evidence_ids,
        customer_reference="Customer A",
    )


def test_acceptance_is_recorded():
    result = make_decision()

    assert result.accepted is True
    assert result.declined is False
    assert result.decision == "accepted"


def test_decline_is_recorded():
    result = make_decision(decision="declined")

    assert result.accepted is False
    assert result.declined is True


def test_tenant_is_preserved():
    result = make_decision()

    assert result.tenant_id == "tenant-1"
    assert result.quote_id == "quote-1"


def test_evidence_is_preserved():
    result = make_decision(
        evidence_ids=("whatsapp-message-1", "quote-message-2")
    )

    assert result.evidence_ids == (
        "whatsapp-message-1",
        "quote-message-2",
    )


def test_decision_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        make_decision(
            decided_at=datetime.now()
        )


def test_future_decision_is_rejected():
    with pytest.raises(ValueError, match="future"):
        make_decision(
            decided_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )


def test_invalid_decision_is_rejected():
    with pytest.raises(ValueError, match="invalid customer decision"):
        make_decision(decision="maybe")


def test_blank_evidence_is_rejected():
    with pytest.raises(
        ValueError,
        match="evidence_ids cannot contain blank values",
    ):
        make_decision(evidence_ids=("evidence-1", ""))


def test_blank_quote_id_is_rejected():
    with pytest.raises(ValueError, match="quote_id is required"):
        CustomerQuoteDecision(
            decision_id="decision-1",
            tenant_id="tenant-1",
            quote_id="",
            decision="accepted",
            decided_at=datetime.now(timezone.utc),
        )


def test_blank_tenant_id_is_rejected():
    with pytest.raises(ValueError, match="tenant_id is required"):
        CustomerQuoteDecision(
            decision_id="decision-1",
            tenant_id="",
            quote_id="quote-1",
            decision="accepted",
            decided_at=datetime.now(timezone.utc),
        )
