from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

import pytest

from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.task_scheduler import ScheduledTask, TaskBudget


def make_task(
    task_id: str = "task-1",
    tenant_id: str = "tenant-a",
    execution_id: str = "exec-1",
) -> ScheduledTask:
    return ScheduledTask(
        task_id=task_id,
        tenant_id=tenant_id,
        execution_id=execution_id,
        priority=1,
        execution_class="standard",
        budget=TaskBudget(max_attempts=3),
    )


def test_only_one_worker_can_start_same_task(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    store.save(make_task())

    barrier = threading.Barrier(2)
    results: list[str] = []
    errors: list[str] = []

    def worker(lease_id: str):
        barrier.wait()
        try:
            store.start(
                "task-1",
                lease_id,
                now=datetime.now(timezone.utc),
            )
            results.append(lease_id)
        except ValueError as exc:
            errors.append(str(exc))

    threads = [
        threading.Thread(target=worker, args=("lease-a",)),
        threading.Thread(target=worker, args=("lease-b",)),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(results) == 1
    assert len(errors) == 1

    recovery = store.recovery("task-1")
    assert recovery.lease_id == results[0]


def test_wrong_worker_cannot_heartbeat(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    store.save(make_task())

    started = datetime.now(timezone.utc)
    store.start("task-1", "lease-a", now=started)

    before = store.recovery("task-1").heartbeat_at

    with pytest.raises(PermissionError):
        store.heartbeat(
            "task-1",
            "lease-b",
            now=started + timedelta(seconds=10),
        )

    after = store.recovery("task-1").heartbeat_at

    assert after == before


def test_concurrent_recovery_only_requeues_once(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    store.save(make_task())

    started = datetime.now(timezone.utc)
    store.start("task-1", "lease-a", now=started)

    recovery_time = started + timedelta(minutes=10)

    barrier = threading.Barrier(2)
    results: list[ScheduledTask] = []

    def recover():
        barrier.wait()
        result = store.recover(
            "task-1",
            stale_after=timedelta(minutes=5),
            now=recovery_time,
        )
        results.append(result)

    threads = [
        threading.Thread(target=recover),
        threading.Thread(target=recover),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    final_task = store.get("task-1")

    assert final_task is not None
    assert final_task.status == "queued"
    assert final_task.attempt == 1

    recovery = store.recovery("task-1")
    assert recovery.recovery_count == 1


def test_completion_and_recovery_cannot_both_win(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    store.save(make_task())

    started = datetime.now(timezone.utc)
    store.start("task-1", "lease-a", now=started)

    race_time = started + timedelta(minutes=10)

    barrier = threading.Barrier(2)
    completed: list[bool] = []
    recovered: list[ScheduledTask] = []

    def complete():
        barrier.wait()
        try:
            store.complete("task-1", "lease-a", now=race_time)
            completed.append(True)
        except (PermissionError, ValueError):
            completed.append(False)

    def recover():
        barrier.wait()
        recovered.append(
            store.recover(
                "task-1",
                stale_after=timedelta(minutes=5),
                now=race_time,
            )
        )

    threads = [
        threading.Thread(target=complete),
        threading.Thread(target=recover),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    final_task = store.get("task-1")
    assert final_task is not None

    assert final_task.status in {"completed", "queued"}
    assert not (
        final_task.status == "completed"
        and final_task.attempt > 0
    )


def test_concurrent_recovery_respects_retry_budget(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")

    task = make_task()
    task = ScheduledTask(
        task_id=task.task_id,
        tenant_id=task.tenant_id,
        execution_id=task.execution_id,
        priority=task.priority,
        execution_class=task.execution_class,
        dependencies=task.dependencies,
        deadline=task.deadline,
        budget=TaskBudget(max_attempts=2),
        status=task.status,
        attempt=task.attempt,
        cancelled=task.cancelled,
    )

    store.save(task)

    started = datetime.now(timezone.utc)
    store.start("task-1", "lease-a", now=started)

    first_recovery = started + timedelta(minutes=10)

    store.recover(
        "task-1",
        stale_after=timedelta(minutes=5),
        now=first_recovery,
    )

    assert store.get("task-1").attempt == 1

    store.start(
        "task-1",
        "lease-b",
        now=first_recovery + timedelta(seconds=1),
    )

    second_recovery = first_recovery + timedelta(minutes=10)

    barrier = threading.Barrier(2)
    results: list[ScheduledTask] = []

    def recover():
        barrier.wait()
        results.append(
            store.recover(
                "task-1",
                stale_after=timedelta(minutes=5),
                now=second_recovery,
            )
        )

    threads = [
        threading.Thread(target=recover),
        threading.Thread(target=recover),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    final_task = store.get("task-1")

    assert final_task is not None
    assert final_task.status == "failed"
    assert final_task.attempt == 1
