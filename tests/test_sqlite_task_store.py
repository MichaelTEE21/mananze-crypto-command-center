from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.task_scheduler import ScheduledTask, TaskBudget


def make_task(
    task_id="task-1",
    tenant_id="tenant-a",
    execution_id="exec-1",
    max_attempts=3,
):
    return ScheduledTask(
        task_id=task_id,
        tenant_id=tenant_id,
        execution_id=execution_id,
        budget=TaskBudget(max_attempts=max_attempts),
    )


def test_task_survives_new_store_instance(tmp_path):
    db = tmp_path / "tasks.db"

    store = SQLiteTaskStore(db)
    task = make_task()
    store.save(task)

    restarted_store = SQLiteTaskStore(db)

    assert restarted_store.get(task.task_id) == task


def test_running_task_and_lease_survive_restart(tmp_path):
    db = tmp_path / "tasks.db"
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    store = SQLiteTaskStore(db)
    task = make_task()
    store.save(task)

    store.start(task.task_id, "lease-1", now)

    restarted_store = SQLiteTaskStore(db)

    loaded = restarted_store.get(task.task_id)
    recovery = restarted_store.recovery(task.task_id)

    assert loaded.status == "running"
    assert recovery.lease_id == "lease-1"
    assert recovery.started_at == now
    assert recovery.heartbeat_at == now


def test_heartbeat_survives_restart(tmp_path):
    db = tmp_path / "tasks.db"
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    heartbeat = started + timedelta(minutes=2)

    store = SQLiteTaskStore(db)
    task = make_task()
    store.save(task)
    store.start(task.task_id, "lease-1", started)
    store.heartbeat(task.task_id, "lease-1", heartbeat)

    restarted_store = SQLiteTaskStore(db)

    assert restarted_store.recovery(
        task.task_id
    ).heartbeat_at == heartbeat


def test_stale_task_can_be_recovered_after_restart(tmp_path):
    db = tmp_path / "tasks.db"
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recovered_at = started + timedelta(minutes=10)

    store = SQLiteTaskStore(db)
    task = make_task(max_attempts=3)
    store.save(task)
    store.start(task.task_id, "lease-1", started)

    restarted_store = SQLiteTaskStore(db)

    recovered = restarted_store.recover(
        task.task_id,
        stale_after=timedelta(minutes=5),
        now=recovered_at,
    )

    assert recovered.status == "queued"
    assert recovered.attempt == 1

    restarted_again = SQLiteTaskStore(db)

    assert restarted_again.get(
        task.task_id
    ).status == "queued"

    assert restarted_again.recovery(
        task.task_id
    ).lease_id is None


def test_completed_task_survives_restart_and_is_not_recovered(tmp_path):
    db = tmp_path / "tasks.db"
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    completed = started + timedelta(minutes=1)
    later = started + timedelta(hours=1)

    store = SQLiteTaskStore(db)
    task = make_task()
    store.save(task)
    store.start(task.task_id, "lease-1", started)
    store.complete(task.task_id, "lease-1", completed)

    restarted_store = SQLiteTaskStore(db)

    result = restarted_store.recover(
        task.task_id,
        stale_after=timedelta(minutes=5),
        now=later,
    )

    assert result.status == "completed"
    assert restarted_store.get(
        task.task_id
    ).status == "completed"


def test_tenant_scoped_stale_detection_survives_restart(tmp_path):
    db = tmp_path / "tasks.db"
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    now = started + timedelta(minutes=10)

    store = SQLiteTaskStore(db)

    task_a = make_task(
        task_id="task-a",
        tenant_id="tenant-a",
        execution_id="exec-a",
    )

    task_b = make_task(
        task_id="task-b",
        tenant_id="tenant-b",
        execution_id="exec-b",
    )

    store.save(task_a)
    store.save(task_b)

    store.start(task_a.task_id, "lease-a", started)
    store.start(task_b.task_id, "lease-b", started)

    restarted_store = SQLiteTaskStore(db)

    stale = restarted_store.stale_running_tasks(
        stale_after=timedelta(minutes=5),
        now=now,
        tenant_id="tenant-a",
    )

    assert [task.task_id for task in stale] == ["task-a"]


def test_wrong_lease_is_rejected_after_restart(tmp_path):
    db = tmp_path / "tasks.db"
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    store = SQLiteTaskStore(db)
    task = make_task()
    store.save(task)
    store.start(task.task_id, "real-lease", now)

    restarted_store = SQLiteTaskStore(db)

    with pytest.raises(PermissionError):
        restarted_store.heartbeat(
            task.task_id,
            "fake-lease",
            now,
        )


def test_retry_budget_survives_restart(tmp_path):
    db = tmp_path / "tasks.db"
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    later = started + timedelta(minutes=10)

    store = SQLiteTaskStore(db)
    task = make_task(max_attempts=1)
    store.save(task)
    store.start(task.task_id, "lease-1", started)

    restarted_store = SQLiteTaskStore(db)

    failed = restarted_store.recover(
        task.task_id,
        stale_after=timedelta(minutes=5),
        now=later,
    )

    assert failed.status == "failed"
    assert failed.attempt == 0


def test_idempotency_key_is_stable(tmp_path):
    db = tmp_path / "tasks.db"

    store = SQLiteTaskStore(db)

    first = store.idempotency_key(
        "tenant-a",
        "task-1",
        "exec-1",
        0,
    )

    second = store.idempotency_key(
        "tenant-a",
        "task-1",
        "exec-1",
        0,
    )

    assert first == second
    assert len(first) == 64


def test_idempotency_key_is_tenant_scoped(tmp_path):
    db = tmp_path / "tasks.db"

    store = SQLiteTaskStore(db)

    tenant_a = store.idempotency_key(
        "tenant-a",
        "task-1",
        "exec-1",
        0,
    )

    tenant_b = store.idempotency_key(
        "tenant-b",
        "task-1",
        "exec-1",
        0,
    )

    assert tenant_a != tenant_b
