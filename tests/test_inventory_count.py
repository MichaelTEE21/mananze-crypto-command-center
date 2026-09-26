import pytest

from mananze_os.inventory_count import InventoryCount


def test_physical_count_with_no_variance() -> None:
    count = InventoryCount(
        count_id="count-001",
        tenant_id="tenant-001",
        item_id="stock-001",
        recorded_quantity=42,
        counted_quantity=42,
        unit="sheet",
    )

    assert count.variance == 0


def test_physical_count_detects_shortage() -> None:
    count = InventoryCount(
        count_id="count-001",
        tenant_id="tenant-001",
        item_id="stock-001",
        recorded_quantity=42,
        counted_quantity=37,
        unit="sheet",
    )

    assert count.variance == -5


def test_physical_count_detects_surplus() -> None:
    count = InventoryCount(
        count_id="count-001",
        tenant_id="tenant-001",
        item_id="stock-001",
        recorded_quantity=37,
        counted_quantity=42,
        unit="sheet",
    )

    assert count.variance == 5


def test_zero_quantities_are_valid() -> None:
    count = InventoryCount(
        "count-001",
        "tenant-001",
        "stock-001",
        0,
        0,
        "piece",
    )

    assert count.variance == 0


def test_negative_recorded_quantity_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="recorded_quantity cannot be negative",
    ):
        InventoryCount(
            "count-001",
            "tenant-001",
            "stock-001",
            -1,
            0,
            "piece",
        )


def test_negative_counted_quantity_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="counted_quantity cannot be negative",
    ):
        InventoryCount(
            "count-001",
            "tenant-001",
            "stock-001",
            0,
            -1,
            "piece",
        )


def test_blank_count_id_rejected() -> None:
    with pytest.raises(ValueError, match="count_id is required"):
        InventoryCount(
            "",
            "tenant-001",
            "stock-001",
            1,
            1,
            "piece",
        )


def test_blank_tenant_id_rejected() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        InventoryCount(
            "count-001",
            "",
            "stock-001",
            1,
            1,
            "piece",
        )


def test_blank_item_id_rejected() -> None:
    with pytest.raises(ValueError, match="item_id is required"):
        InventoryCount(
            "count-001",
            "tenant-001",
            "",
            1,
            1,
            "piece",
        )


def test_blank_unit_rejected() -> None:
    with pytest.raises(ValueError, match="unit is required"):
        InventoryCount(
            "count-001",
            "tenant-001",
            "stock-001",
            1,
            1,
            "",
        )


def test_blank_evidence_id_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="evidence_ids cannot contain blank values",
    ):
        InventoryCount(
            "count-001",
            "tenant-001",
            "stock-001",
            1,
            1,
            "piece",
            evidence_ids=("evidence-001", ""),
        )


def test_count_is_immutable() -> None:
    count = InventoryCount(
        "count-001",
        "tenant-001",
        "stock-001",
        10,
        9,
        "piece",
    )

    with pytest.raises(AttributeError):
        count.counted_quantity = 10
