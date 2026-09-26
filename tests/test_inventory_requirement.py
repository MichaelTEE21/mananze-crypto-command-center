import pytest

from mananze_os.inventory import InventoryItem
from mananze_os.inventory_availability import InventoryAvailability
from mananze_os.inventory_requirement import assess_inventory_requirement
from mananze_os.inventory_reservation import InventoryReservation


def make_availability(
    quantity_on_hand: float = 30,
    reserved_quantity: float = 18,
) -> InventoryAvailability:
    item = InventoryItem(
        item_id="stock-001",
        tenant_id="tenant-001",
        name="Board",
        unit="sheet",
        quantity_on_hand=quantity_on_hand,
    )

    reservations = []

    if reserved_quantity > 0:
        reservations.append(
            InventoryReservation(
                reservation_id="reservation-001",
                tenant_id="tenant-001",
                item_id="stock-001",
                quantity=reserved_quantity,
                unit="sheet",
                job_id="job-001",
            )
        )

    return InventoryAvailability.calculate(item, reservations)


def test_requirement_is_satisfied_when_available_stock_is_enough() -> None:
    availability = make_availability()

    result = assess_inventory_requirement(
        requirement_id="requirement-001",
        quantity_required=12,
        availability=availability,
    )

    assert result.status == "satisfied"
    assert result.satisfied is True
    assert result.quantity_required == 12
    assert result.quantity_available == 12
    assert result.shortage_quantity == 0


def test_requirement_is_satisfied_when_stock_exceeds_requirement() -> None:
    availability = make_availability(
        quantity_on_hand=30,
        reserved_quantity=10,
    )

    result = assess_inventory_requirement(
        requirement_id="requirement-001",
        quantity_required=15,
        availability=availability,
    )

    assert result.status == "satisfied"
    assert result.shortage_quantity == 0


def test_shortage_is_calculated_when_stock_is_insufficient() -> None:
    availability = make_availability()

    result = assess_inventory_requirement(
        requirement_id="requirement-001",
        quantity_required=15,
        availability=availability,
    )

    assert result.status == "shortage"
    assert result.satisfied is False
    assert result.quantity_available == 12
    assert result.shortage_quantity == 3


def test_full_shortage_when_nothing_is_available() -> None:
    availability = make_availability(
        quantity_on_hand=0,
        reserved_quantity=0,
    )

    result = assess_inventory_requirement(
        requirement_id="requirement-001",
        quantity_required=15,
        availability=availability,
    )

    assert result.status == "shortage"
    assert result.shortage_quantity == 15


def test_over_reserved_stock_produces_explicit_shortage() -> None:
    availability = make_availability(
        quantity_on_hand=10,
        reserved_quantity=15,
    )

    result = assess_inventory_requirement(
        requirement_id="requirement-001",
        quantity_required=5,
        availability=availability,
    )

    assert result.status == "shortage"
    assert result.quantity_available == -5
    assert result.shortage_quantity == 10


def test_tenant_and_item_identity_are_preserved() -> None:
    availability = make_availability()

    result = assess_inventory_requirement(
        requirement_id="requirement-001",
        quantity_required=10,
        availability=availability,
    )

    assert result.tenant_id == "tenant-001"
    assert result.item_id == "stock-001"
    assert result.unit == "sheet"


def test_blank_requirement_id_rejected() -> None:
    availability = make_availability()

    with pytest.raises(ValueError, match="requirement_id is required"):
        assess_inventory_requirement(
            requirement_id="",
            quantity_required=10,
            availability=availability,
        )


def test_zero_requirement_rejected() -> None:
    availability = make_availability()

    with pytest.raises(
        ValueError,
        match="quantity_required must be greater than zero",
    ):
        assess_inventory_requirement(
            requirement_id="requirement-001",
            quantity_required=0,
            availability=availability,
        )


def test_negative_requirement_rejected() -> None:
    availability = make_availability()

    with pytest.raises(
        ValueError,
        match="quantity_required must be greater than zero",
    ):
        assess_inventory_requirement(
            requirement_id="requirement-001",
            quantity_required=-1,
            availability=availability,
        )


def test_assessment_does_not_mutate_availability() -> None:
    availability = make_availability()

    assess_inventory_requirement(
        requirement_id="requirement-001",
        quantity_required=15,
        availability=availability,
    )

    assert availability.quantity_on_hand == 30
    assert availability.quantity_reserved == 18
    assert availability.quantity_available == 12
