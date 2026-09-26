from mananze_os.quote import Quote, QuoteLine


def make_line(
    *,
    line_id="line-1",
    quote_id="quote-1",
    tenant_id="tenant-1",
    quantity=2,
    unit_price=100,
):
    return QuoteLine(
        line_id=line_id,
        quote_id=quote_id,
        tenant_id=tenant_id,
        description="Board",
        line_type="material",
        quantity=quantity,
        unit="sheet",
        unit_price=unit_price,
        currency="ZAR",
        evidence_ids=("evidence-1",),
    )


def test_quote_line_calculates_line_total():
    line = make_line(quantity=3, unit_price=125)

    assert line.line_total == 375


def test_quote_calculates_subtotal():
    quote = Quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        lines=(
            make_line(line_id="line-1", quantity=2, unit_price=100),
            make_line(line_id="line-2", quantity=3, unit_price=50),
        ),
    )

    assert quote.subtotal == 350


def test_quote_requires_identity():
    try:
        Quote(
            quote_id="",
            tenant_id="tenant-1",
            customer_reference="Customer A",
            currency="ZAR",
        )
    except ValueError as exc:
        assert "quote_id" in str(exc)
    else:
        raise AssertionError("Expected quote_id validation")


def test_quote_rejects_mismatched_line_quote():
    try:
        Quote(
            quote_id="quote-1",
            tenant_id="tenant-1",
            customer_reference="Customer A",
            currency="ZAR",
            lines=(
                make_line(quote_id="different-quote"),
            ),
        )
    except ValueError as exc:
        assert "quote_id" in str(exc)
    else:
        raise AssertionError("Expected quote line quote_id validation")


def test_quote_rejects_mismatched_line_tenant():
    try:
        Quote(
            quote_id="quote-1",
            tenant_id="tenant-1",
            customer_reference="Customer A",
            currency="ZAR",
            lines=(
                make_line(tenant_id="tenant-2"),
            ),
        )
    except ValueError as exc:
        assert "tenant_id" in str(exc)
    else:
        raise AssertionError("Expected quote line tenant validation")


def test_quote_rejects_mismatched_currency():
    line = QuoteLine(
        line_id="line-1",
        quote_id="quote-1",
        tenant_id="tenant-1",
        description="Board",
        line_type="material",
        quantity=1,
        unit="sheet",
        unit_price=100,
        currency="USD",
    )

    try:
        Quote(
            quote_id="quote-1",
            tenant_id="tenant-1",
            customer_reference="Customer A",
            currency="ZAR",
            lines=(line,),
        )
    except ValueError as exc:
        assert "currency" in str(exc)
    else:
        raise AssertionError("Expected currency validation")


def test_negative_unit_price_is_rejected():
    try:
        make_line(unit_price=-1)
    except ValueError as exc:
        assert "unit_price" in str(exc)
    else:
        raise AssertionError("Expected negative price validation")


def test_zero_quantity_is_rejected():
    try:
        make_line(quantity=0)
    except ValueError as exc:
        assert "quantity" in str(exc)
    else:
        raise AssertionError("Expected quantity validation")
