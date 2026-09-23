from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.task_recovery import DurableTaskStore
from mananze_os.task_scheduler import ScheduledTask, TaskBudget


def make_task(
    *,
    task_id: str = "task-1",
    tenant_id: str = "tenant-a",
    execution_id: str = "exec-1",
    max_attempts: int = 3,
) -> ScheduledTask:
    return ScheduledTask(
        task_id=task_id,
        tenant_id=tenant_id,
        execution_id=execution_id,
        budget=TaskBudget(max_attempts=max_attempts),
    )


def test_task_can_be_persisted_and_reloaded():
    store = DurableTaskStore()
    task = make_task()

    store.save(task)

    assert store.get(task.task_id) == task


def test_task_start_records_lease_and_heartbeat():
    store = DurableTaskStore()
    task = make_task()
    store.save(task)

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    running = store.start(task.task_id, "lease-1", now)

    assert running.status == "running"
    record = store.recovery(task.task_id)
    assert record.lease_id == "lease-1"
    assert record.started_at == now
    assert record.heartbeat_at == now


def test_heartbeat_requires_current_lease():
    store = DurableTaskStore()
    store.save(make_task())

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.start("task-1", "lease-1", now)

    with pytest.raises(PermissionError):
        store.heartbeat(
            "task-1",
            "wrong-lease",
            now + timedelta(seconds=1),
        )


def test_stale_running_task_is_detected():
    store = DurableTaskStore()
    store.save(make_task())

    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.start("task-1", "lease-1", started)

    stale = store.stale_running_tasks(
        timedelta(minutes=5),
        now=started + timedelta(minutes=6),
    )

    assert [task.task_id for task in stale] == ["task-1"]


def test_active_running_task_is_not_recovered():
    store = DurableTaskStore()
    store.save(make_task())

    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.start("task-1", "lease-1", started)

    with pytest.raises(ValueError, match="lease is still active"):
        store.recover(
            "task-1",
            timedelta(minutes=5),
            now=started + timedelta(minutes=1),
        )


def test_stale_task_recovers_to_queued_and_increments_attempt():
    store = DurableTaskStore()
    store.save(make_task(max_attempts=3))

    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.start("task-1", "lease-1", started)

    recovered = store.recover(
        "task-1",
        timedelta(minutes=5),
        now=started + timedelta(minutes=6),
    )

    assert recovered.status == "queued"
    assert recovered.attempt == 1

    record = store.recovery("task-1")
    assert record.lease_id is None
    assert record.recovery_count == 1
    assert "stale execution lease" in record.last_recovery_reason


def test_recovery_is_idempotent():
    store = DurableTaskStore()
    store.save(make_task(max_attempts=3))

    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.start("task-1", "lease-1", started)

    first = store.recover(
        "task-1",
        timedelta(minutes=5),
        now=started + timedelta(minutes=6),
    )

    second = store.recover(
        "task-1",
        timedelta(minutes=5),
        now=started + timedelta(minutes=7),
    )

    assert second == first
    assert store.recovery("task-1").recovery_count == 1


def test_completed_task_is_never_recovered():
    store = DurableTaskStore()
    store.save(make_task())

    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.start("task-1", "lease-1", started)
    completed = store.complete(
        "task-1",
        "lease-1",
        started + timedelta(seconds=1),
    )

    recovered = store.recover(
        "task-1",
        timedelta(minutes=5),
        now=started + timedelta(days=1),
    )

    assert recovered == completed
    assert recovered.status == "completed"


def test_cancelled_task_is_never_recovered():
    store = DurableTaskStore()
    store.save(make_task())

    task = store.get("task-1")
    cancelled = task.__class__(
        task_id=task.task_id,
        tenant_id=task.tenant_id,
        execution_id=task.execution_id,
        status="cancelled",
        cancelled=True,
    )
    store.update(cancelled)

    recovered = store.recover(
        "task-1",
        timedelta(minutes=5),
        now=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert recovered.status == "cancelled"


def test_retry_budget_is_enforced_during_recovery():
    store = DurableTaskStore()
    store.save(make_task(max_attempts=1))

    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.start("task-1", "lease-1", started)

    recovered = store.recover(
        "task-1",
        timedelta(minutes=5),
        now=started + timedelta(minutes=6),
    )

    assert recovered.status == "failed"
    assert recovered.attempt == 0


def test_tenant_scoped_stale_detection_does_not_cross_tenants():
    store = DurableTaskStore()
    store.save(make_task(task_id="task-a", tenant_id="tenant-a"))
    store.save(
        make_task(
            task_id="task-b",
            tenant_id="tenant-b",
            execution_id="exec-b",
        )
    )

    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.start("task-a", "lease-a", started)
    store.start("task-b", "lease-b", started)

    stale = store.stale_running_tasks(
        timedelta(minutes=5),
        now=started + timedelta(minutes=6),
        tenant_id="tenant-a",
    )

    assert [task.task_id for task in stale] == ["task-a"]


def test_idempotency_key_is_deterministic():
    first = DurableTaskStore.idempotency_key(
        "task-1",
        "exec-1",
        0,
    )
    second = DurableTaskStore.idempotency_key(
        "task-1",
        "exec-1",
        0,
    )

    assert first == second
    assert len(first) == 64


def test_different_attempts_have_different_idempotency_keys():
    first = DurableTaskStore.idempotency_key(
        "task-1",
        "exec-1",
        0,
    )
    second = DurableTaskStore.idempotency_key(
        "task-1",
        "exec-1",
        1,
    )

    assert first != second


def test_tenant_and_execution_identity_cannot_change():
    store = DurableTaskStore()
    store.save(make_task())

    task = store.get("task-1")

    with pytest.raises(PermissionError):
        store.update(
            ScheduledTask(
                task_id=task.task_id,
                tenant_id="tenant-b",
                execution_id=task.execution_id,
            )
        )

    with pytest.raises(ValueError):
        store.update(
            ScheduledTask(
                task_id=task.task_id,
                tenant_id=task.tenant_id,
                execution_id="different-execution",
            )
        )
