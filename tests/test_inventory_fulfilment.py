from mananze_os.fulfilment_strategy import FulfilmentStrategy
from mananze_os.inventory import InventoryItem
from mananze_os.inventory_fulfilment import assess_inventory_fulfilment


def make_strategy(tenant_id="tenant-1"):
    return FulfilmentStrategy(
        strategy_id="strategy-1",
        tenant_id=tenant_id,
        strategy_type="inventory_first",
        name="Inventory first",
        confirmation_status="confirmed",
    )


def make_item(tenant_id="tenant-1", quantity=10):
    return InventoryItem(
        item_id="board-1",
        tenant_id=tenant_id,
        name="Board",
        unit="sheet",
        quantity_on_hand=quantity,
    )


def test_sufficient_inventory_has_no_shortage():
    result = assess_inventory_fulfilment(
        job_id="job-1",
        requirement_id="req-1",
        quantity_required=5,
        item=make_item(quantity=10),
        reservations=[],
        strategy=make_strategy(),
    )

    assert result.requirement.status == "satisfied"
    assert result.shortage is None
    assert result.availability.quantity_available == 10


def test_insufficient_inventory_creates_shortage():
    result = assess_inventory_fulfilment(
        job_id="job-1",
        requirement_id="req-1",
        quantity_required=8,
        item=make_item(quantity=5),
        reservations=[],
        strategy=make_strategy(),
    )

    assert result.requirement.status == "shortage"
    assert result.shortage is not None
    assert result.shortage.shortage_quantity == 3


def test_reservations_reduce_available_inventory():
    from mananze_os.inventory_reservation import InventoryReservation

    reservation = InventoryReservation(
        reservation_id="res-1",
        tenant_id="tenant-1",
        item_id="board-1",
        quantity=4,
        unit="sheet",
        job_id="other-job",
    )

    result = assess_inventory_fulfilment(
        job_id="job-1",
        requirement_id="req-1",
        quantity_required=7,
        item=make_item(quantity=10),
        reservations=[reservation],
        strategy=make_strategy(),
    )

    assert result.availability.quantity_available == 6
    assert result.requirement.status == "shortage"
    assert result.shortage.shortage_quantity == 1


def test_tenant_mismatch_is_rejected():
    try:
        assess_inventory_fulfilment(
            job_id="job-1",
            requirement_id="req-1",
            quantity_required=5,
            item=make_item(tenant_id="tenant-1"),
            reservations=[],
            strategy=make_strategy(tenant_id="tenant-2"),
        )
    except ValueError as exc:
        assert "tenant" in str(exc)
    else:
        raise AssertionError("Expected tenant mismatch to raise ValueError")


def test_mismatched_reservation_tenant_is_rejected():
    from mananze_os.inventory_reservation import InventoryReservation

    reservation = InventoryReservation(
        reservation_id="res-1",
        tenant_id="tenant-2",
        item_id="board-1",
        quantity=2,
        unit="sheet",
        job_id="other-job",
    )

    try:
        assess_inventory_fulfilment(
            job_id="job-1",
            requirement_id="req-1",
            quantity_required=5,
            item=make_item(),
            reservations=[reservation],
            strategy=make_strategy(),
        )
    except ValueError as exc:
        assert "tenant" in str(exc)
    else:
        raise AssertionError("Expected reservation tenant mismatch to raise ValueError")
