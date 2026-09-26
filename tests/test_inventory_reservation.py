import pytest

from mananze_os.inventory_reservation import InventoryReservation


def test_valid_reservation() -> None:
    reservation = InventoryReservation(
        reservation_id="reservation-001",
        tenant_id="tenant-001",
        item_id="stock-001",
        quantity=18,
        unit="piece",
        job_id="job-101",
    )

    assert reservation.quantity == 18
    assert reservation.job_id == "job-101"
    assert reservation.status == "reserved"


def test_supported_statuses() -> None:
    statuses = (
        "reserved",
        "released",
        "consumed",
        "cancelled",
    )

    for index, status in enumerate(statuses):
        reservation = InventoryReservation(
            reservation_id=f"reservation-{index}",
            tenant_id="tenant-001",
            item_id="stock-001",
            quantity=1,
            unit="piece",
            job_id="job-101",
            status=status,
        )

        assert reservation.status == status


def test_reservation_does_not_change_quantity_semantically() -> None:
    reservation = InventoryReservation(
        reservation_id="reservation-001",
        tenant_id="tenant-001",
        item_id="stock-001",
        quantity=18,
        unit="piece",
        job_id="job-101",
    )

    assert reservation.quantity == 18


def test_zero_quantity_rejected() -> None:
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        InventoryReservation(
            "reservation-001",
            "tenant-001",
            "stock-001",
            0,
            "piece",
            "job-101",
        )


def test_negative_quantity_rejected() -> None:
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        InventoryReservation(
            "reservation-001",
            "tenant-001",
            "stock-001",
            -1,
            "piece",
            "job-101",
        )


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        InventoryReservation(
            "reservation-001",
            "tenant-001",
            "stock-001",
            1,
            "piece",
            "job-101",
            status="invalid",  # type: ignore[arg-type]
        )


def test_blank_reservation_id_rejected() -> None:
    with pytest.raises(ValueError, match="reservation_id is required"):
        InventoryReservation(
            "",
            "tenant-001",
            "stock-001",
            1,
            "piece",
            "job-101",
        )


def test_blank_tenant_id_rejected() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        InventoryReservation(
            "reservation-001",
            "",
            "stock-001",
            1,
            "piece",
            "job-101",
        )


def test_blank_item_id_rejected() -> None:
    with pytest.raises(ValueError, match="item_id is required"):
        InventoryReservation(
            "reservation-001",
            "tenant-001",
            "",
            1,
            "piece",
            "job-101",
        )


def test_blank_unit_rejected() -> None:
    with pytest.raises(ValueError, match="unit is required"):
        InventoryReservation(
            "reservation-001",
            "tenant-001",
            "stock-001",
            1,
            "",
            "job-101",
        )


def test_blank_job_id_rejected() -> None:
    with pytest.raises(ValueError, match="job_id is required"):
        InventoryReservation(
            "reservation-001",
            "tenant-001",
            "stock-001",
            1,
            "piece",
            "",
        )


def test_reservation_is_immutable() -> None:
    reservation = InventoryReservation(
        "reservation-001",
        "tenant-001",
        "stock-001",
        1,
        "piece",
        "job-101",
    )

    with pytest.raises(AttributeError):
        reservation.quantity = 2
