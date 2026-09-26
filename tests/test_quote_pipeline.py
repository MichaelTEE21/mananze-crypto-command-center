from mananze_os.pricing_resolution import PricingResolution
from mananze_os.quote_pipeline import prepare_quote
from mananze_os.requirement_validation import (
    RequirementValidationFinding,
    RequirementValidationResult,
)


def make_validation(
    disposition="pass",
):
    finding = RequirementValidationFinding(
        check_id="test:requirement",
        disposition=disposition,
        message="Test validation finding",
    )

    return RequirementValidationResult(
        validation_id="validation:test",
        tenant_id="tenant-1",
        requirement_id="requirement-1",
        findings=(finding,),
    )


def make_resolution():
    from mananze_os.pricing_resolution import resolve_unit_price
    from mananze_os.pricing_rule import PricingRule

    rule = PricingRule(
        rule_id="rule-1",
        tenant_id="tenant-1",
        name="Board price",
        rule_type="unit_price",
        value=250,
        currency="ZAR",
        applies_to="material:board",
        confirmation_status="confirmed",
    )

    return resolve_unit_price(
        quote_id="quote-1",
        tenant_id="tenant-1",
        line_id="line-1",
        description="Board",
        quantity=2,
        unit="sheet",
        applies_to="material:board",
        currency="ZAR",
        rules=[rule],
    )


def test_prepare_quote_creates_ready_pipeline():
    result = prepare_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        validation=make_validation("pass"),
        pricing_resolutions=[make_resolution()],
    )

    assert result.quote is not None
    assert result.build.ready is True
    assert result.readiness is not None
    assert result.ready_to_send is True
    assert result.must_freeze is False


def test_validation_review_blocks_automatic_send():
    result = prepare_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        validation=make_validation("review_required"),
        pricing_resolutions=[make_resolution()],
    )

    assert result.quote is not None
    assert result.readiness is not None
    assert result.ready_to_send is False
    assert result.must_freeze is True


def test_validation_conflict_blocks_automatic_send():
    result = prepare_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        validation=make_validation("conflict"),
        pricing_resolutions=[make_resolution()],
    )

    assert result.ready_to_send is False
    assert result.must_freeze is True


def test_validation_insufficient_evidence_blocks_automatic_send():
    result = prepare_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        validation=make_validation("insufficient_evidence"),
        pricing_resolutions=[make_resolution()],
    )

    assert result.ready_to_send is False
    assert result.must_freeze is True


def test_unresolved_pricing_blocks_before_readiness():
    unresolved = PricingResolution(
        status="no_rule",
        message="No confirmed pricing rule matches the requirement.",
    )

    result = prepare_quote(
        quote_id="quote-1",
        tenant_id="tenant-1",
        customer_reference="Customer A",
        currency="ZAR",
        validation=make_validation("pass"),
        pricing_resolutions=[unresolved],
    )

    assert result.quote is None
    assert result.readiness is None
    assert result.ready_to_send is False
    assert result.must_freeze is True


def test_tenant_mismatch_is_rejected():
    validation = RequirementValidationResult(
        validation_id="validation:test",
        tenant_id="tenant-2",
        requirement_id="requirement-1",
        findings=(
            RequirementValidationFinding(
                check_id="test:requirement",
                disposition="pass",
                message="Valid",
            ),
        ),
    )

    try:
        prepare_quote(
            quote_id="quote-1",
            tenant_id="tenant-1",
            customer_reference="Customer A",
            currency="ZAR",
            validation=validation,
            pricing_resolutions=[make_resolution()],
        )
    except ValueError as exc:
        assert "tenant" in str(exc)
    else:
        raise AssertionError("Expected tenant mismatch to raise ValueError")
