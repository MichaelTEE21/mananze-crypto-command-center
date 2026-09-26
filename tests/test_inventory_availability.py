from mananze_os.inventory import InventoryItem
from mananze_os.inventory_availability import InventoryAvailability
from mananze_os.inventory_reservation import InventoryReservation


def test_available_equals_on_hand_when_nothing_is_reserved() -> None:
    item = InventoryItem(
        item_id="stock-001",
        tenant_id="tenant-001",
        name="Board",
        unit="sheet",
        quantity_on_hand=30,
    )

    result = InventoryAvailability.calculate(item, [])

    assert result.quantity_on_hand == 30
    assert result.quantity_reserved == 0
    assert result.quantity_available == 30


def test_reserved_stock_is_subtracted_from_available_stock() -> None:
    item = InventoryItem(
        item_id="stock-001",
        tenant_id="tenant-001",
        name="Board",
        unit="sheet",
        quantity_on_hand=30,
    )

    reservation = InventoryReservation(
        reservation_id="reservation-001",
        tenant_id="tenant-001",
        item_id="stock-001",
        quantity=18,
        unit="sheet",
        job_id="job-001",
    )

    result = InventoryAvailability.calculate(item, [reservation])

    assert result.quantity_on_hand == 30
    assert result.quantity_reserved == 18
    assert result.quantity_available == 12


def test_multiple_active_reservations_are_combined() -> None:
    item = InventoryItem(
        item_id="stock-001",
        tenant_id="tenant-001",
        name="Board",
        unit="sheet",
        quantity_on_hand=30,
    )

    reservations = [
        InventoryReservation(
            "reservation-001",
            "tenant-001",
            "stock-001",
            10,
            "sheet",
            "job-001",
        ),
        InventoryReservation(
            "reservation-002",
            "tenant-001",
            "stock-001",
            8,
            "sheet",
            "job-002",
        ),
    ]

    result = InventoryAvailability.calculate(item, reservations)

    assert result.quantity_reserved == 18
    assert result.quantity_available == 12


def test_released_reservation_is_not_reserved_stock() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Board",
        "sheet",
        30,
    )

    reservation = InventoryReservation(
        "reservation-001",
        "tenant-001",
        "stock-001",
        18,
        "sheet",
        "job-001",
        status="released",
    )

    result = InventoryAvailability.calculate(item, [reservation])

    assert result.quantity_reserved == 0
    assert result.quantity_available == 30


def test_consumed_reservation_is_not_active_reservation() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Board",
        "sheet",
        30,
    )

    reservation = InventoryReservation(
        "reservation-001",
        "tenant-001",
        "stock-001",
        18,
        "sheet",
        "job-001",
        status="consumed",
    )

    result = InventoryAvailability.calculate(item, [reservation])

    assert result.quantity_reserved == 0
    assert result.quantity_available == 30


def test_cancelled_reservation_is_not_active_reservation() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Board",
        "sheet",
        30,
    )

    reservation = InventoryReservation(
        "reservation-001",
        "tenant-001",
        "stock-001",
        18,
        "sheet",
        "job-001",
        status="cancelled",
    )

    result = InventoryAvailability.calculate(item, [reservation])

    assert result.quantity_reserved == 0
    assert result.quantity_available == 30


def test_other_tenant_reservation_is_ignored() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Board",
        "sheet",
        30,
    )

    reservation = InventoryReservation(
        "reservation-001",
        "tenant-002",
        "stock-001",
        18,
        "sheet",
        "job-001",
    )

    result = InventoryAvailability.calculate(item, [reservation])

    assert result.quantity_reserved == 0
    assert result.quantity_available == 30


def test_other_item_reservation_is_ignored() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Board",
        "sheet",
        30,
    )

    reservation = InventoryReservation(
        "reservation-001",
        "tenant-001",
        "stock-002",
        18,
        "sheet",
        "job-001",
    )

    result = InventoryAvailability.calculate(item, [reservation])

    assert result.quantity_reserved == 0
    assert result.quantity_available == 30


def test_different_unit_reservation_is_ignored() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Board",
        "sheet",
        30,
    )

    reservation = InventoryReservation(
        "reservation-001",
        "tenant-001",
        "stock-001",
        18,
        "piece",
        "job-001",
    )

    result = InventoryAvailability.calculate(item, [reservation])

    assert result.quantity_reserved == 0
    assert result.quantity_available == 30


def test_availability_does_not_mutate_inventory() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Board",
        "sheet",
        30,
    )

    reservation = InventoryReservation(
        "reservation-001",
        "tenant-001",
        "stock-001",
        18,
        "sheet",
        "job-001",
    )

    InventoryAvailability.calculate(item, [reservation])

    assert item.quantity_on_hand == 30


def test_availability_can_be_negative_when_reservations_exceed_stock() -> None:
    item = InventoryItem(
        "stock-001",
        "tenant-001",
        "Board",
        "sheet",
        10,
    )

    reservation = InventoryReservation(
        "reservation-001",
        "tenant-001",
        "stock-001",
        15,
        "sheet",
        "job-001",
    )

    result = InventoryAvailability.calculate(item, [reservation])

    assert result.quantity_reserved == 15
    assert result.quantity_available == -5
