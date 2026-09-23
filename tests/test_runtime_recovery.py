from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.runtime import MananzeRuntime
from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.task_scheduler import ScheduledTask, TaskBudget
from mananze_os.task_scheduler import TaskScheduler


def make_task(task_id="task:recovery"):
    return ScheduledTask(
        task_id=task_id,
        tenant_id="tenant-a",
        execution_id="exec:recovery",
        priority=0,
        execution_class="standard",
        budget=TaskBudget(max_attempts=3),
    )


def test_runtime_requires_durable_store_for_recovery():
    runtime = MananzeRuntime()

    with pytest.raises(RuntimeError, match="durable task recovery"):
        runtime.recover_stale_tasks(timedelta(minutes=1))


def test_runtime_recovers_stale_task(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    runtime = MananzeRuntime(task_store=store)

    task = make_task()
    store.save(task)

    started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recovery_now = started_at + timedelta(minutes=10)

    store.start(
        task_id=task.task_id,
        lease_id="lease:old",
        now=started_at,
    )

    recovered = runtime.recover_stale_tasks(
        stale_after=timedelta(minutes=5),
        limit=10,
        now=recovery_now,
    )

    assert len(recovered) == 1
    assert recovered[0].task_id == task.task_id
    assert recovered[0].status == "queued"
    assert recovered[0].attempt == 1

    recovery = store.recovery(task.task_id)
    assert recovery.lease_id is None
    assert recovery.recovery_count == 1
    assert recovery.last_recovery_reason == "stale execution lease"


def test_old_lease_cannot_complete_after_runtime_recovery(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    runtime = MananzeRuntime(task_store=store)

    task = make_task()
    store.save(task)

    started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recovery_now = started_at + timedelta(minutes=10)

    store.start(
        task_id=task.task_id,
        lease_id="lease:old",
        now=started_at,
    )

    runtime.recover_stale_tasks(
        stale_after=timedelta(minutes=5),
        now=recovery_now,
    )

    store.start(
        task_id=task.task_id,
        lease_id="lease:new",
        now=recovery_now,
    )

    with pytest.raises(PermissionError, match="not running under"):
        store.complete(
            task.task_id,
            "lease:old",
            now=recovery_now + timedelta(minutes=1),
        )

    completed = store.complete(
        task.task_id,
        "lease:new",
        now=recovery_now + timedelta(minutes=2),
    )

    assert completed.status == "completed"


def test_runtime_recovery_respects_tenant_and_limit(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    runtime = MananzeRuntime(task_store=store)

    task_a = make_task("task:a")
    task_b = ScheduledTask(
        task_id="task:b",
        tenant_id="tenant-b",
        execution_id="exec:b",
        priority=0,
        execution_class="standard",
        budget=TaskBudget(max_attempts=3),
    )

    store.save(task_a)
    store.save(task_b)

    stale_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recovery_now = stale_time + timedelta(minutes=10)

    store.start("task:a", "lease:a", now=stale_time)
    store.start("task:b", "lease:b", now=stale_time)

    recovered = runtime.recover_stale_tasks(
        stale_after=timedelta(minutes=5),
        tenant_id="tenant-a",
        limit=1,
        now=recovery_now,
    )

    assert tuple(task.task_id for task in recovered) == ("task:a",)
    assert store.get("task:a").status == "queued"
    assert store.get("task:b").status == "running"


def test_recovered_task_is_visible_to_scheduler_for_new_worker_claim(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    runtime = MananzeRuntime(task_store=store)
    scheduler = runtime.task_scheduler

    task = ScheduledTask(
        task_id="task:worker-restart",
        tenant_id="tenant-a",
        execution_id="exec:worker-restart",
        priority=10,
        budget=TaskBudget(max_attempts=3),
    )

    runtime.task_scheduler.submit(task)
    store.save(task)

    first_lease = "lease:first-worker"
    first_now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    stale_now = first_now + timedelta(minutes=10)

    store.start(
        task_id=task.task_id,
        lease_id=first_lease,
        now=first_now,
    )
    store.heartbeat(
        task_id=task.task_id,
        lease_id=first_lease,
        now=first_now,
    )

    recovered = runtime.recover_stale_tasks(
        stale_after=timedelta(minutes=5),
        tenant_id="tenant-a",
        now=stale_now,
    )[0]

    assert recovered.status == "queued"
    assert recovered.attempt == 1

    scheduler.restore_queued(recovered)

    selected = scheduler.next_task(
        tenant_id="tenant-a",
        now=stale_now,
    )

    assert selected is not None
    assert selected.task_id == task.task_id
    assert selected.status == "queued"

    second_lease = "lease:second-worker"

    claimed = store.start(
        task_id=selected.task_id,
        lease_id=second_lease,
        now=stale_now,
    )

    assert claimed.status == "running"
    assert store.recovery(task.task_id).lease_id == second_lease

    with pytest.raises(
        PermissionError,
        match="task is not running under the supplied lease",
    ):
        store.complete(
            task_id=task.task_id,
            lease_id=first_lease,
            now=stale_now,
        )

    completed = store.complete(
        task_id=task.task_id,
        lease_id=second_lease,
        now=stale_now,
    )

    assert completed.status == "completed"
