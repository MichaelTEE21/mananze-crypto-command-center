import pytest

from mananze_os.inventory import InventoryItem


def test_valid_inventory_item() -> None:
    item = InventoryItem(
        item_id="stock-001",
        tenant_id="tenant-001",
        name="Soft-close hinge",
        unit="piece",
        quantity_on_hand=37,
    )

    assert item.name == "Soft-close hinge"
    assert item.unit == "piece"
    assert item.quantity_on_hand == 37


def test_inventory_supports_different_units() -> None:
    items = (
        InventoryItem("stock-001", "tenant-001", "16mm White Board", "sheet", 42),
        InventoryItem("stock-002", "tenant-001", "White Edging", "metre", 125),
        InventoryItem("stock-003", "tenant-001", "Screws", "box", 8),
        InventoryItem("stock-004", "tenant-001", "Glue", "litre", 12),
        InventoryItem("stock-005", "tenant-001", "Oven", "piece", 3),
    )

    assert [item.unit for item in items] == [
        "sheet",
        "metre",
        "box",
        "litre",
        "piece",
    ]


def test_zero_stock_is_valid() -> None:
    item = InventoryItem(
        item_id="stock-001",
        tenant_id="tenant-001",
        name="18mm Premium Board",
        unit="sheet",
        quantity_on_hand=0,
    )

    assert item.quantity_on_hand == 0


def test_negative_stock_rejected() -> None:
    with pytest.raises(ValueError, match="quantity_on_hand cannot be negative"):
        InventoryItem(
            item_id="stock-001",
            tenant_id="tenant-001",
            name="Hinge",
            unit="piece",
            quantity_on_hand=-1,
        )


def test_blank_item_id_rejected() -> None:
    with pytest.raises(ValueError, match="item_id is required"):
        InventoryItem("", "tenant-001", "Hinge", "piece", 10)


def test_blank_tenant_id_rejected() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        InventoryItem("stock-001", "", "Hinge", "piece", 10)


def test_blank_name_rejected() -> None:
    with pytest.raises(ValueError, match="name is required"):
        InventoryItem("stock-001", "tenant-001", "", "piece", 10)


def test_blank_unit_rejected() -> None:
    with pytest.raises(ValueError, match="unit is required"):
        InventoryItem("stock-001", "tenant-001", "Hinge", "", 10)


def test_inventory_item_is_immutable() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Hinge",
        "piece",
        10,
    )

    with pytest.raises(AttributeError):
        item.quantity_on_hand = 20
