from datetime import datetime, timedelta, timezone

from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.task_scheduler import ScheduledTask, TaskBudget


def make_retryable_task(store):
    task = ScheduledTask(
        task_id="task-crash-recovery",
        tenant_id="tenant-a",
        execution_id="exec-crash-recovery",
        budget=TaskBudget(max_attempts=3),
    )
    store.save(task)
    return task


def test_idempotency_operation_can_be_reclaimed_after_stale_task_recovery(
    tmp_path,
):
    db = tmp_path / "tasks.db"
    store = SQLiteTaskStore(db)

    task = make_retryable_task(store)

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

    record = store.idempotency_record(
        tenant_id=task.tenant_id,
        operation_key=operation_key,
    )

    assert record is not None
    assert record["status"] == "in_progress"
    assert record["lease_id"] == "lease-A"

    # Simulate the worker disappearing. The heartbeat is now stale.
    stale_now = started + timedelta(minutes=10)

    recovered = store.recover(
        task.task_id,
        stale_after=timedelta(minutes=5),
        now=stale_now,
    )

    assert recovered.attempt == 1

    # The recovered task is started by a new worker with a new lease.
    store.start(
        task_id=task.task_id,
        lease_id="lease-B",
        now=stale_now,
    )

    reclaimed = store.claim_operation(
        tenant_id=task.tenant_id,
        operation_key=operation_key,
        task_id=task.task_id,
        execution_id=task.execution_id,
        lease_id="lease-B",
        now=stale_now,
    )

    assert reclaimed is True

    record = store.idempotency_record(
        tenant_id=task.tenant_id,
        operation_key=operation_key,
    )

    assert record is not None
    assert record["status"] == "in_progress"
    assert record["lease_id"] == "lease-B"

    completed = store.complete_operation(
        tenant_id=task.tenant_id,
        operation_key=operation_key,
        lease_id="lease-B",
        result={"status": "success"},
        evidence={"recovered": True},
        now=stale_now,
    )

    assert completed["status"] == "completed"
    assert completed["lease_id"] == "lease-B"
    assert completed["result_json"] == '{"status": "success"}'
