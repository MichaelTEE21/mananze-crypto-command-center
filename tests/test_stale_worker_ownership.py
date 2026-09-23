from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.task_scheduler import ScheduledTask, TaskBudget


def test_stale_worker_cannot_complete_after_lease_transfer(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")

    task = ScheduledTask(
        task_id="task-stale-owner",
        tenant_id="tenant-a",
        execution_id="exec-stale-owner",
        budget=TaskBudget(max_attempts=3),
    )
    store.save(task)

    started = datetime(
        2026,
        1,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    store.start(
        task_id=task.task_id,
        lease_id="lease-A",
        now=started,
    )

    operation_key = store.operation_key(
        task.tenant_id,
        task.task_id,
        task.execution_id,
        "controlled-execution",
    )

    assert store.claim_operation(
        tenant_id=task.tenant_id,
        operation_key=operation_key,
        task_id=task.task_id,
        execution_id=task.execution_id,
        lease_id="lease-A",
        now=started,
    )

    stale_now = started + timedelta(minutes=10)

    recovered = store.recover(
        task.task_id,
        stale_after=timedelta(minutes=5),
        now=stale_now,
    )

    assert recovered.attempt == 1

    store.start(
        task_id=task.task_id,
        lease_id="lease-B",
        now=stale_now,
    )

    assert store.claim_operation(
        tenant_id=task.tenant_id,
        operation_key=operation_key,
        task_id=task.task_id,
        execution_id=task.execution_id,
        lease_id="lease-B",
        now=stale_now,
    )

    with pytest.raises(PermissionError, match="supplied lease"):
        store.complete_operation(
            tenant_id=task.tenant_id,
            operation_key=operation_key,
            lease_id="lease-A",
            result={"status": "stale-worker"},
        )

    record = store.idempotency_record(
        tenant_id=task.tenant_id,
        operation_key=operation_key,
    )

    assert record["status"] == "in_progress"
    assert record["lease_id"] == "lease-B"

    completed = store.complete_operation(
        tenant_id=task.tenant_id,
        operation_key=operation_key,
        lease_id="lease-B",
        result={"status": "success"},
        evidence={"worker": "B"},
        now=stale_now,
    )

    assert completed["status"] == "completed"
    assert completed["lease_id"] == "lease-B"
