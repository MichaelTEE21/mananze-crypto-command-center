from mananze_os.pricing_resolution import resolve_unit_price
from mananze_os.pricing_rule import PricingRule


def make_rule(
    *,
    rule_id="rule-1",
    tenant_id="tenant-1",
    applies_to="material:board",
    value=250,
    currency="ZAR",
    confirmation_status="confirmed",
):
    return PricingRule(
        rule_id=rule_id,
        tenant_id=tenant_id,
        name="Board price",
        rule_type="unit_price",
        value=value,
        currency=currency,
        applies_to=applies_to,
        evidence_ids=(f"evidence:{rule_id}",),
        confirmation_status=confirmation_status,
    )


def test_matching_rule_resolves_quote_line():
    result = resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id="line-1",
        description="Board",
        quantity=2,
        unit="sheet",
        applies_to="material:board",
        currency="ZAR",
        rules=[make_rule(value=250)],
    )

    assert result.resolved is True
    assert result.requires_exception is False
    assert result.quote_line is not None
    assert result.quote_line.unit_price == 250
    assert result.quote_line.line_total == 500


def test_no_matching_rule_creates_exception():
    result = resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id="line-1",
        description="Board",
        quantity=2,
        unit="sheet",
        applies_to="material:unknown",
        currency="ZAR",
        rules=[make_rule()],
    )

    assert result.status == "no_rule"
    assert result.quote_line is None
    assert result.requires_exception is True


def test_multiple_matching_rules_create_conflict():
    result = resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id="line-1",
        description="Board",
        quantity=2,
        unit="sheet",
        applies_to="material:board",
        currency="ZAR",
        rules=[
            make_rule(rule_id="rule-1", value=250),
            make_rule(rule_id="rule-2", value=275),
        ],
    )

    assert result.status == "conflict"
    assert result.quote_line is None
    assert result.requires_exception is True


def test_unconfirmed_rule_cannot_price_automatically():
    result = resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id="line-1",
        description="Board",
        quantity=2,
        unit="sheet",
        applies_to="material:board",
        currency="ZAR",
        rules=[make_rule(confirmation_status="unconfirmed")],
    )

    assert result.status == "no_rule"


def test_wrong_tenant_rule_is_ignored():
    result = resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id="line-1",
        description="Board",
        quantity=2,
        unit="sheet",
        applies_to="material:board",
        currency="ZAR",
        rules=[make_rule(tenant_id="tenant-2")],
    )

    assert result.status == "no_rule"


def test_wrong_currency_rule_is_ignored():
    result = resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id="line-1",
        description="Board",
        quantity=2,
        unit="sheet",
        applies_to="material:board",
        currency="ZAR",
        rules=[make_rule(currency="USD")],
    )

    assert result.status == "no_rule"


def test_pricing_evidence_is_carried_into_quote_line():
    result = resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id="line-1",
        description="Board",
        quantity=1,
        unit="sheet",
        applies_to="material:board",
        currency="ZAR",
        rules=[make_rule(rule_id="price-list-7")],
    )

    assert result.quote_line is not None
    assert result.quote_line.evidence_ids == ("evidence:price-list-7",)
