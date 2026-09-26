import pytest

from mananze_os.inventory_movement import InventoryMovement


def test_valid_receipt_movement() -> None:
    movement = InventoryMovement(
        movement_id="movement-001",
        tenant_id="tenant-001",
        item_id="stock-001",
        movement_type="receipt",
        quantity=20,
        unit="sheet",
        reason="Supplier delivery",
        reference="PO-1001",
        evidence_ids=("delivery-001",),
    )

    assert movement.movement_type == "receipt"
    assert movement.quantity == 20
    assert movement.reference == "PO-1001"


def test_supported_movement_types() -> None:
    movement_types = (
        "receipt",
        "consumption",
        "adjustment",
        "return",
        "damage",
        "correction",
    )

    for index, movement_type in enumerate(movement_types):
        movement = InventoryMovement(
            movement_id=f"movement-{index}",
            tenant_id="tenant-001",
            item_id="stock-001",
            movement_type=movement_type,
            quantity=1,
            unit="piece",
            reason="Test movement",
        )

        assert movement.movement_type == movement_type


def test_zero_quantity_rejected() -> None:
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        InventoryMovement(
            "movement-001",
            "tenant-001",
            "stock-001",
            "receipt",
            0,
            "piece",
            "Test",
        )


def test_negative_quantity_rejected() -> None:
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        InventoryMovement(
            "movement-001",
            "tenant-001",
            "stock-001",
            "receipt",
            -1,
            "piece",
            "Test",
        )


def test_invalid_movement_type_rejected() -> None:
    with pytest.raises(ValueError, match="invalid movement_type"):
        InventoryMovement(
            "movement-001",
            "tenant-001",
            "stock-001",
            "invalid",  # type: ignore[arg-type]
            1,
            "piece",
            "Test",
        )


def test_blank_movement_id_rejected() -> None:
    with pytest.raises(ValueError, match="movement_id is required"):
        InventoryMovement(
            "",
            "tenant-001",
            "stock-001",
            "receipt",
            1,
            "piece",
            "Test",
        )


def test_blank_tenant_id_rejected() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        InventoryMovement(
            "movement-001",
            "",
            "stock-001",
            "receipt",
            1,
            "piece",
            "Test",
        )


def test_blank_item_id_rejected() -> None:
    with pytest.raises(ValueError, match="item_id is required"):
        InventoryMovement(
            "movement-001",
            "tenant-001",
            "",
            "receipt",
            1,
            "piece",
            "Test",
        )


def test_blank_unit_rejected() -> None:
    with pytest.raises(ValueError, match="unit is required"):
        InventoryMovement(
            "movement-001",
            "tenant-001",
            "stock-001",
            "receipt",
            1,
            "",
            "Test",
        )


def test_blank_reason_rejected() -> None:
    with pytest.raises(ValueError, match="reason is required"):
        InventoryMovement(
            "movement-001",
            "tenant-001",
            "stock-001",
            "receipt",
            1,
            "piece",
            "",
        )


def test_blank_evidence_id_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="evidence_ids cannot contain blank values",
    ):
        InventoryMovement(
            "movement-001",
            "tenant-001",
            "stock-001",
            "receipt",
            1,
            "piece",
            "Test",
            evidence_ids=("evidence-001", ""),
        )


def test_movement_is_immutable() -> None:
    movement = InventoryMovement(
        "movement-001",
        "tenant-001",
        "stock-001",
        "receipt",
        1,
        "piece",
        "Test",
    )

    with pytest.raises(AttributeError):
        movement.quantity = 2
