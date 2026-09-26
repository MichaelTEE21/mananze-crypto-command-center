import pytest

from mananze_os.job_lifecycle import (
    advance_job_lifecycle,
    create_job_lifecycle,
)


def test_new_job_starts_at_fulfilment_pending():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    assert lifecycle.job_id == "job-1"
    assert lifecycle.tenant_id == "tenant-1"
    assert lifecycle.stage == "fulfilment_pending"


@pytest.mark.parametrize(
    ("stage", "expected"),
    [
        ("inventory_pending", "inventory_pending"),
        ("procurement_pending", "procurement_pending"),
        ("make_to_order_pending", "make_to_order_pending"),
        ("service_delivery_pending", "service_delivery_pending"),
    ],
)
def test_fulfilment_path_can_be_selected(stage, expected):
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    result = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage=stage,
    )

    assert result.stage == expected


def test_inventory_can_move_to_work():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )

    assert lifecycle.stage == "in_progress"


def test_procurement_can_move_to_work():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="procurement_pending",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )

    assert lifecycle.stage == "in_progress"


def test_work_can_move_to_qc():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="qc_pending",
    )

    assert lifecycle.stage == "qc_pending"


def test_qc_can_move_to_delivery():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="qc_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="delivery_pending",
    )

    assert lifecycle.stage == "delivery_pending"


def test_qc_can_move_to_collection():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="qc_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="collection_pending",
    )

    assert lifecycle.stage == "collection_pending"


def test_delivery_can_complete():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="qc_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="delivery_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="completed",
    )

    assert lifecycle.stage == "completed"


def test_collection_can_complete():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="qc_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="collection_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="completed",
    )

    assert lifecycle.stage == "completed"


def test_invalid_transition_is_rejected():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    with pytest.raises(ValueError, match="invalid lifecycle transition"):
        advance_job_lifecycle(
            lifecycle=lifecycle,
            stage="completed",
        )


def test_completed_job_cannot_move():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="qc_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="delivery_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="completed",
    )

    with pytest.raises(ValueError, match="invalid lifecycle transition"):
        advance_job_lifecycle(
            lifecycle=lifecycle,
            stage="in_progress",
        )


def test_evidence_is_preserved():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
        evidence_ids=("evidence-1",),
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )

    assert lifecycle.evidence_ids == ("evidence-1",)


def test_transition_does_not_mutate_previous_state():
    original = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    updated = advance_job_lifecycle(
        lifecycle=original,
        stage="inventory_pending",
    )

    assert original.stage == "fulfilment_pending"
    assert updated.stage == "inventory_pending"


def test_on_hold_can_resume():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="on_hold",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="in_progress",
    )

    assert lifecycle.stage == "in_progress"


def test_job_can_be_cancelled_before_completion():
    lifecycle = create_job_lifecycle(
        job_id="job-1",
        tenant_id="tenant-1",
    )

    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="inventory_pending",
    )
    lifecycle = advance_job_lifecycle(
        lifecycle=lifecycle,
        stage="cancelled",
    )

    assert lifecycle.stage == "cancelled"
