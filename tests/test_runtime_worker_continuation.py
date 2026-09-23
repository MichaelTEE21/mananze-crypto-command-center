from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.runtime import MananzeRuntime
from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.task_scheduler import TaskBudget, ScheduledTask


def make_task():
    return ScheduledTask(
        task_id="task:runtime-worker",
        tenant_id="tenant-a",
        execution_id="exec:runtime-worker",
        budget=TaskBudget(max_attempts=3),
    )


def test_runtime_worker_continuation_survives_stale_worker(tmp_path):
    store = SQLiteTaskStore(str(tmp_path / "runtime-worker.db"))
    runtime = MananzeRuntime(
        tenants=(),
        authorities=(),
        permissions=(),
        task_store=store,
    )

    task = make_task()
    runtime.task_scheduler.submit(task)
    store.save(task)

    first_lease = "lease:worker:first"
    first_now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    claimed = runtime.claim_next_task(
        tenant_id="tenant-a",
        lease_id=first_lease,
        now=first_now,
    )

    assert claimed is not None
    assert claimed.status == "running"
    assert claimed.attempt == 0

    heartbeated = runtime.heartbeat_task(
        task_id=claimed.task_id,
        lease_id=first_lease,
        now=first_now,
    )

    assert heartbeated.status == "running"

    stale_now = first_now + timedelta(minutes=10)

    recovered = runtime.recover_stale_tasks(
        stale_after=timedelta(minutes=5),
        now=stale_now,
        tenant_id="tenant-a",
    )

    assert len(recovered) == 1
    assert recovered[0].status == "queued"
    assert recovered[0].attempt == 1

    second_lease = "lease:worker:second"

    reclaimed = runtime.claim_next_task(
        tenant_id="tenant-a",
        lease_id=second_lease,
        now=stale_now,
    )

    assert reclaimed is not None
    assert reclaimed.status == "running"
    assert reclaimed.attempt == 1

    with pytest.raises(PermissionError):
        runtime.complete_task(
            task_id=reclaimed.task_id,
            lease_id=first_lease,
            now=stale_now,
        )

    completed = runtime.complete_task(
        task_id=reclaimed.task_id,
        lease_id=second_lease,
        now=stale_now,
    )

    assert completed.status == "completed"

    durable = store.get("task:runtime-worker")
    assert durable is not None
    assert durable.status == "completed"

