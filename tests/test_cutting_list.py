import pytest

from mananze_os.cutting_list import CuttingListItem


def test_valid_cutting_list_item() -> None:
    item = CuttingListItem(
        item_id="item-001",
        tenant_id="tenant-001",
        material="Melamine",
        dimensions="2120 x 600",
        quantity=2,
        thickness="16mm",
        edging="2mm front edge",
        backer="3mm",
        finish="White",
        evidence_ids=("evidence-001",),
        confirmation_status="confirmed",
    )

    assert item.dimensions == "2120 x 600"
    assert item.quantity == 2
    assert item.thickness == "16mm"


def test_cutting_list_preserves_supplied_dimensions_exactly() -> None:
    item = CuttingListItem(
        item_id="item-001",
        tenant_id="tenant-001",
        material="Board",
        dimensions="2120 x 600",
    )

    assert item.dimensions == "2120 x 600"


def test_cutting_list_item_is_immutable() -> None:
    item = CuttingListItem(
        item_id="item-001",
        tenant_id="tenant-001",
        material="Board",
        dimensions="2120 x 600",
    )

    with pytest.raises(AttributeError):
        item.dimensions = "2400 x 600"


def test_blank_item_id_rejected() -> None:
    with pytest.raises(ValueError, match="item_id is required"):
        CuttingListItem(
            item_id="",
            tenant_id="tenant-001",
            material="Board",
            dimensions="2120 x 600",
        )


def test_blank_tenant_id_rejected() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        CuttingListItem(
            item_id="item-001",
            tenant_id="",
            material="Board",
            dimensions="2120 x 600",
        )


def test_blank_material_rejected() -> None:
    with pytest.raises(ValueError, match="material is required"):
        CuttingListItem(
            item_id="item-001",
            tenant_id="tenant-001",
            material="",
            dimensions="2120 x 600",
        )


def test_blank_dimensions_rejected() -> None:
    with pytest.raises(ValueError, match="dimensions are required"):
        CuttingListItem(
            item_id="item-001",
            tenant_id="tenant-001",
            material="Board",
            dimensions="",
        )


def test_nonpositive_quantity_rejected() -> None:
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        CuttingListItem(
            item_id="item-001",
            tenant_id="tenant-001",
            material="Board",
            dimensions="2120 x 600",
            quantity=0,
        )


def test_blank_evidence_id_rejected() -> None:
    with pytest.raises(ValueError, match="evidence_ids cannot contain blank values"):
        CuttingListItem(
            item_id="item-001",
            tenant_id="tenant-001",
            material="Board",
            dimensions="2120 x 600",
            evidence_ids=("evidence-001", ""),
        )


def test_invalid_confirmation_status_rejected() -> None:
    with pytest.raises(ValueError, match="invalid confirmation_status"):
        CuttingListItem(
            item_id="item-001",
            tenant_id="tenant-001",
            material="Board",
            dimensions="2120 x 600",
            confirmation_status="invalid",  # type: ignore[arg-type]
        )
