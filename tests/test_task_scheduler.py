import pytest
from datetime import datetime, timezone, timedelta

from mananze_os.task_scheduler import ScheduledTask, TaskBudget, TaskScheduler


def test_submit_and_get_task():
    scheduler = TaskScheduler()
    task = ScheduledTask(
        task_id="task-1",
        tenant_id="tenant-1",
        execution_id="exec-1",
    )

    scheduler.submit(task)

    assert scheduler.get("task-1") == task


def test_priority_determines_next_task():
    scheduler = TaskScheduler()

    scheduler.submit(
        ScheduledTask(
            task_id="low",
            tenant_id="tenant-1",
            execution_id="exec-low",
            priority=1,
        )
    )
    scheduler.submit(
        ScheduledTask(
            task_id="high",
            tenant_id="tenant-1",
            execution_id="exec-high",
            priority=10,
        )
    )

    assert scheduler.next_task("tenant-1").task_id == "high"


def test_deadline_breaks_priority_tie():
    scheduler = TaskScheduler()
    now = datetime.now(timezone.utc)

    scheduler.submit(
        ScheduledTask(
            task_id="later",
            tenant_id="tenant-1",
            execution_id="exec-later",
            priority=5,
            deadline=now + timedelta(hours=2),
        )
    )
    scheduler.submit(
        ScheduledTask(
            task_id="sooner",
            tenant_id="tenant-1",
            execution_id="exec-sooner",
            priority=5,
            deadline=now + timedelta(hours=1),
        )
    )

    assert scheduler.next_task("tenant-1", now=now).task_id == "sooner"


def test_dependency_blocks_task_until_completed():
    scheduler = TaskScheduler()

    scheduler.submit(
        ScheduledTask(
            task_id="dependency",
            tenant_id="tenant-1",
            execution_id="exec-dependency",
        )
    )
    scheduler.submit(
        ScheduledTask(
            task_id="dependent",
            tenant_id="tenant-1",
            execution_id="exec-dependent",
            dependencies=("dependency",),
        )
    )

    assert scheduler.is_eligible("dependent") is False
    assert scheduler.next_task("tenant-1").task_id == "dependency"

    scheduler.mark_running("dependency")
    scheduler.mark_completed("dependency")

    assert scheduler.is_eligible("dependent") is True
    assert scheduler.next_task("tenant-1").task_id == "dependent"


def test_cross_tenant_dependency_is_not_eligible():
    scheduler = TaskScheduler()

    scheduler.submit(
        ScheduledTask(
            task_id="dependency",
            tenant_id="tenant-2",
            execution_id="exec-dependency",
        )
    )
    scheduler.submit(
        ScheduledTask(
            task_id="dependent",
            tenant_id="tenant-1",
            execution_id="exec-dependent",
            dependencies=("dependency",),
        )
    )

    assert scheduler.is_eligible("dependent") is False


def test_cancelled_task_cannot_run():
    scheduler = TaskScheduler()

    scheduler.submit(
        ScheduledTask(
            task_id="task-1",
            tenant_id="tenant-1",
            execution_id="exec-1",
        )
    )

    scheduler.cancel("task-1")

    assert scheduler.get("task-1").status == "cancelled"
    assert scheduler.next_task("tenant-1") is None


def test_retry_respects_attempt_budget():
    scheduler = TaskScheduler()

    scheduler.submit(
        ScheduledTask(
            task_id="task-1",
            tenant_id="tenant-1",
            execution_id="exec-1",
            budget=TaskBudget(max_attempts=2),
        )
    )

    scheduler.mark_running("task-1")
    scheduler.mark_failed("task-1")

    retried = scheduler.retry("task-1")

    assert retried.status == "queued"
    assert retried.attempt == 1

    scheduler.mark_running("task-1")
    scheduler.mark_failed("task-1")

    with pytest.raises(ValueError, match="retry budget exhausted"):
        scheduler.retry("task-1")


def test_duplicate_task_is_rejected():
    scheduler = TaskScheduler()

    task = ScheduledTask(
        task_id="task-1",
        tenant_id="tenant-1",
        execution_id="exec-1",
    )

    scheduler.submit(task)

    with pytest.raises(ValueError, match="already registered"):
        scheduler.submit(task)


def test_invalid_budget_is_rejected():
    with pytest.raises(ValueError, match="max_attempts"):
        TaskBudget(max_attempts=0)

    with pytest.raises(ValueError, match="token_budget"):
        TaskBudget(token_budget=0)

    with pytest.raises(ValueError, match="concurrency_limit"):
        TaskBudget(concurrency_limit=0)


def test_task_state_transitions_are_controlled():
    scheduler = TaskScheduler()

    scheduler.submit(
        ScheduledTask(
            task_id="task-1",
            tenant_id="tenant-1",
            execution_id="exec-1",
        )
    )

    with pytest.raises(ValueError):
        scheduler.mark_completed("task-1")

    scheduler.mark_running("task-1")
    scheduler.mark_completed("task-1")

    with pytest.raises(ValueError):
        scheduler.mark_failed("task-1")
from datetime import datetime, timezone

import pytest

from mananze_os.task_scheduler import ScheduledTask, TaskBudget, TaskScheduler


def test_missing_dependency_does_not_make_scheduler_crash():
    scheduler = TaskScheduler()

    scheduler.submit(
        ScheduledTask(
            task_id="dependent",
            tenant_id="tenant-1",
            execution_id="exec-1",
            dependencies=("missing-task",),
        )
    )

    assert scheduler.is_eligible("dependent") is False
    assert scheduler.next_task("tenant-1") is None


def test_concurrency_limit_prevents_parallel_tasks_in_same_execution():
    scheduler = TaskScheduler()

    budget = TaskBudget(concurrency_limit=1)

    scheduler.submit(
        ScheduledTask(
            task_id="task-1",
            tenant_id="tenant-1",
            execution_id="exec-1",
            budget=budget,
        )
    )
    scheduler.submit(
        ScheduledTask(
            task_id="task-2",
            tenant_id="tenant-1",
            execution_id="exec-1",
            budget=budget,
        )
    )

    scheduler.mark_running("task-1")

    assert scheduler.is_eligible("task-2") is False


def test_concurrency_limit_allows_configured_parallelism():
    scheduler = TaskScheduler()

    budget = TaskBudget(concurrency_limit=2)

    scheduler.submit(
        ScheduledTask(
            task_id="task-1",
            tenant_id="tenant-1",
            execution_id="exec-1",
            budget=budget,
        )
    )
    scheduler.submit(
        ScheduledTask(
            task_id="task-2",
            tenant_id="tenant-1",
            execution_id="exec-1",
            budget=budget,
        )
    )

    scheduler.mark_running("task-1")

    assert scheduler.is_eligible("task-2") is True


def test_concurrency_is_isolated_between_executions():
    scheduler = TaskScheduler()

    budget = TaskBudget(concurrency_limit=1)

    scheduler.submit(
        ScheduledTask(
            task_id="task-1",
            tenant_id="tenant-1",
            execution_id="exec-1",
            budget=budget,
        )
    )
    scheduler.submit(
        ScheduledTask(
            task_id="task-2",
            tenant_id="tenant-1",
            execution_id="exec-2",
            budget=budget,
        )
    )

    scheduler.mark_running("task-1")

    assert scheduler.is_eligible("task-2") is True


def test_concurrency_is_tenant_scoped():
    scheduler = TaskScheduler()

    budget = TaskBudget(concurrency_limit=1)

    scheduler.submit(
        ScheduledTask(
            task_id="task-1",
            tenant_id="tenant-1",
            execution_id="exec-1",
            budget=budget,
        )
    )
    scheduler.submit(
        ScheduledTask(
            task_id="task-2",
            tenant_id="tenant-2",
            execution_id="exec-1",
            budget=budget,
        )
    )

    scheduler.mark_running("task-1")

    assert scheduler.is_eligible("task-2") is True
import pytest

from mananze_os.task_scheduler import (
    ProcessingMode,
    ScheduledTask,
    TaskScheduler,
    is_request_blocking_mode,
)


def test_all_processing_modes_are_supported():
    modes: tuple[ProcessingMode, ...] = (
        "sync",
        "fast",
        "async",
        "background",
        "event",
        "batch",
    )

    for index, mode in enumerate(modes):
        task = ScheduledTask(
            task_id=f"mode-{index}",
            tenant_id="tenant-1",
            execution_id=f"exec-{index}",
            execution_class=mode,
        )

        assert task.processing_mode == mode


@pytest.mark.parametrize(
    "mode",
    ("standard", "sync", "fast"),
)
def test_request_blocking_modes_are_explicit(mode):
    task = ScheduledTask(
        task_id=f"blocking-{mode}",
        tenant_id="tenant-1",
        execution_id=f"exec-{mode}",
        execution_class=mode,
    )

    assert task.request_blocking is True
    assert is_request_blocking_mode(mode) is True


@pytest.mark.parametrize(
    "mode",
    ("async", "background", "event", "batch"),
)
def test_non_blocking_modes_are_explicit(mode):
    task = ScheduledTask(
        task_id=f"non-blocking-{mode}",
        tenant_id="tenant-1",
        execution_id=f"exec-{mode}",
        execution_class=mode,
    )

    assert task.request_blocking is False
    assert is_request_blocking_mode(mode) is False


def test_unsupported_processing_mode_is_rejected():
    with pytest.raises(ValueError, match="unsupported processing mode"):
        ScheduledTask(
            task_id="invalid-mode",
            tenant_id="tenant-1",
            execution_id="exec-1",
            execution_class="unknown",
        )


def test_processing_mode_does_not_bypass_scheduler_governance():
    scheduler = TaskScheduler()

    task = ScheduledTask(
        task_id="async-task",
        tenant_id="tenant-1",
        execution_id="exec-1",
        execution_class="async",
    )

    scheduler.submit(task)

    assert scheduler.get("async-task").processing_mode == "async"
    assert scheduler.next_task("tenant-1").task_id == "async-task"

    scheduler.mark_running("async-task")
    scheduler.mark_completed("async-task")

    assert scheduler.get("async-task").status == "completed"
