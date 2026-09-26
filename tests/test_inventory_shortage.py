import pytest

from mananze_os.inventory_shortage import InventoryShortage


def make_shortage(**overrides):
    values = {
        "shortage_id": "shortage-001",
        "tenant_id": "tenant-001",
        "job_id": "job-001",
        "requirement_id": "requirement-001",
        "item_id": "stock-001",
        "unit": "sheet",
        "quantity_required": 15,
        "quantity_available": 12,
        "shortage_quantity": 3,
        "reason": "Insufficient available stock",
    }
    values.update(overrides)
    return InventoryShortage(**values)


def test_valid_shortage() -> None:
    shortage = make_shortage()

    assert shortage.shortage_id == "shortage-001"
    assert shortage.quantity_required == 15
    assert shortage.quantity_available == 12
    assert shortage.shortage_quantity == 3
    assert shortage.status == "open"


def test_supported_statuses() -> None:
    for status in ("open", "resolved", "cancelled"):
        shortage = make_shortage(status=status)
        assert shortage.status == status


def test_blank_shortage_id_rejected() -> None:
    with pytest.raises(ValueError, match="shortage_id is required"):
        make_shortage(shortage_id="")


def test_blank_tenant_id_rejected() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        make_shortage(tenant_id="")


def test_blank_job_id_rejected() -> None:
    with pytest.raises(ValueError, match="job_id is required"):
        make_shortage(job_id="")


def test_blank_requirement_id_rejected() -> None:
    with pytest.raises(ValueError, match="requirement_id is required"):
        make_shortage(requirement_id="")


def test_blank_item_id_rejected() -> None:
    with pytest.raises(ValueError, match="item_id is required"):
        make_shortage(item_id="")


def test_blank_unit_rejected() -> None:
    with pytest.raises(ValueError, match="unit is required"):
        make_shortage(unit="")


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        make_shortage(status="invalid")


def test_zero_required_quantity_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="quantity_required must be greater than zero",
    ):
        make_shortage(quantity_required=0)


def test_negative_shortage_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="shortage_quantity must be greater than zero",
    ):
        make_shortage(shortage_quantity=-1)


def test_zero_shortage_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="shortage_quantity must be greater than zero",
    ):
        make_shortage(shortage_quantity=0)


def test_blank_reason_rejected() -> None:
    with pytest.raises(ValueError, match="reason is required"):
        make_shortage(reason="")


def test_blank_evidence_id_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="evidence_ids cannot contain blank values",
    ):
        make_shortage(evidence_ids=("evidence-001", ""))


def test_evidence_is_preserved() -> None:
    shortage = make_shortage(
        evidence_ids=("photo-001", "count-001"),
    )

    assert shortage.evidence_ids == ("photo-001", "count-001")


def test_shortage_is_immutable() -> None:
    shortage = make_shortage()

    with pytest.raises(AttributeError):
        shortage.status = "resolved"
