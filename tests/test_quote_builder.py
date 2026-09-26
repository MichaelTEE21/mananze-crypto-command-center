from mananze_os.pricing_resolution import (
    PricingResolution,
    resolve_unit_price,
)
from mananze_os.pricing_rule import PricingRule
from mananze_os.quote_builder import build_quote


def make_rule(
    *,
    rule_id="rule-1",
    applies_to="material:board",
    value=250,
):
    return PricingRule(
        rule_id=rule_id,
        tenant_id="tenant-1",
        name="Price",
        rule_type="unit_price",
        value=value,
        currency="ZAR",
        applies_to=applies_to,
        evidence_ids=(f"evidence:{rule_id}",),
        confirmation_status="confirmed",
    )


def make_resolution(
    *,
    line_id="line-1",
    applies_to="material:board",
    quantity=2,
    value=250,
):
    return resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id=line_id,
        description=applies_to,
        quantity=quantity,
        unit="unit",
        applies_to=applies_to,
        currency="ZAR",
        rules=[make_rule(value=value, applies_to=applies_to)],
    )


def test_builds_complete_quote_from_resolved_lines():
    result = build_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        resolutions=[
            make_resolution(
                line_id="line-1",
                applies_to="material:board",
                quantity=2,
                value=250,
            ),
            make_resolution(
                line_id="line-2",
                applies_to="labour:cutting",
                quantity=1,
                value=500,
            ),
        ],
    )

    assert result.ready is True
    assert result.blocked is False
    assert result.quote is not None
    assert len(result.quote.lines) == 2
    assert result.quote.subtotal == 1000
    assert result.quote.status == "ready"


def test_unresolved_pricing_blocks_complete_quote():
    unresolved = PricingResolution(
        status="no_rule",
        message="No confirmed pricing rule matches the requirement.",
    )

    result = build_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        resolutions=[
            make_resolution(),
            unresolved,
        ],
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.quote is None
    assert "no_rule" in result.reason


def test_conflicting_pricing_blocks_complete_quote():
    conflict = PricingResolution(
        status="conflict",
        message="Multiple confirmed pricing rules match the requirement.",
    )

    result = build_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        resolutions=[conflict],
    )

    assert result.blocked is True
    assert result.quote is None
    assert "conflict" in result.reason


def test_empty_resolutions_block_quote():
    result = build_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        resolutions=[],
    )

    assert result.blocked is True
    assert result.quote is None


def test_quote_evidence_is_preserved():
    result = build_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        resolutions=[make_resolution()],
        evidence_ids=("request-1", "price-list-1"),
    )

    assert result.quote is not None
    assert result.quote.evidence_ids == (
        "request-1",
        "price-list-1",
    )


def test_quote_remains_tenant_scoped():
    result = build_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        resolutions=[make_resolution()],
    )

    assert result.quote is not None
    assert result.quote.tenant_id == "tenant-1"
    assert all(
        line.tenant_id == "tenant-1"
        for line in result.quote.lines
    )
