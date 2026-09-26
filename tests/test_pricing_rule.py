from datetime import date

from mananze_os.pricing_rule import PricingRule


def make_rule(**overrides):
    values = {
        "rule_id": "rule-1",
        "tenant_id": "tenant-1",
        "name": "Board price",
        "rule_type": "unit_price",
        "value": 250.0,
        "currency": "ZAR",
        "applies_to": "board:example",
        "evidence_ids": ("price-list-1",),
        "confirmation_status": "confirmed",
    }
    values.update(overrides)
    return PricingRule(**values)


def test_pricing_rule_is_tenant_scoped():
    rule = make_rule()

    assert rule.tenant_id == "tenant-1"
    assert rule.currency == "ZAR"


def test_pricing_rule_preserves_business_specific_target():
    rule = make_rule(applies_to="material:tenant-specific-premium")

    assert rule.applies_to == "material:tenant-specific-premium"


def test_effective_date_range():
    rule = make_rule(
        effective_from=date(2026, 1, 1),
        effective_until=date(2026, 12, 31),
    )

    assert rule.is_effective_on(date(2026, 6, 1)) is True
    assert rule.is_effective_on(date(2025, 12, 31)) is False
    assert rule.is_effective_on(date(2027, 1, 1)) is False


def test_open_ended_rule_can_be_effective():
    rule = make_rule(effective_from=date(2026, 1, 1))

    assert rule.is_effective_on(date(2026, 9, 26)) is True


def test_invalid_date_range_is_rejected():
    try:
        make_rule(
            effective_from=date(2026, 12, 31),
            effective_until=date(2026, 1, 1),
        )
    except ValueError as exc:
        assert "effective_until" in str(exc)
    else:
        raise AssertionError("Expected invalid date range")


def test_negative_value_is_rejected():
    try:
        make_rule(value=-1)
    except ValueError as exc:
        assert "value" in str(exc)
    else:
        raise AssertionError("Expected negative value validation")


def test_invalid_rule_type_is_rejected():
    try:
        make_rule(rule_type="unknown")
    except ValueError as exc:
        assert "rule_type" in str(exc)
    else:
        raise AssertionError("Expected invalid rule type validation")


def test_evidence_is_preserved():
    rule = make_rule(evidence_ids=("doc-1", "doc-2"))

    assert rule.evidence_ids == ("doc-1", "doc-2")


def test_unconfirmed_rule_remains_unconfirmed():
    rule = make_rule(confirmation_status="unconfirmed")

    assert rule.confirmation_status == "unconfirmed"
