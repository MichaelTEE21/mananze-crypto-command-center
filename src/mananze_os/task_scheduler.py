"""Mananze OS AI-native task scheduling foundation."""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Literal


TaskStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
]

ProcessingMode = Literal[
    "standard",
    "sync",
    "fast",
    "async",
    "background",
    "event",
    "batch",
]


_REQUEST_BLOCKING_MODES = frozenset({"standard", "sync", "fast"})
_NON_BLOCKING_MODES = frozenset({"async", "background", "event", "batch"})
_ALL_PROCESSING_MODES = _REQUEST_BLOCKING_MODES | _NON_BLOCKING_MODES


def is_request_blocking_mode(processing_mode: ProcessingMode) -> bool:
    """Return whether the processing mode is allowed to block a request path."""
    if processing_mode not in _ALL_PROCESSING_MODES:
        raise ValueError(f"unsupported processing mode: {processing_mode}")

    return processing_mode in _REQUEST_BLOCKING_MODES


@dataclass(frozen=True)
class TaskBudget:
    """Resource limits attached to one AI task."""

    max_attempts: int = 1
    time_budget_seconds: float | None = None
    token_budget: int | None = None
    cost_budget: float | None = None
    concurrency_limit: int = 1

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if self.time_budget_seconds is not None and self.time_budget_seconds <= 0:
            raise ValueError("time_budget_seconds must be positive")

        if self.token_budget is not None and self.token_budget <= 0:
            raise ValueError("token_budget must be positive")

        if self.cost_budget is not None and self.cost_budget < 0:
            raise ValueError("cost_budget cannot be negative")

        if self.concurrency_limit < 1:
            raise ValueError("concurrency_limit must be at least 1")


@dataclass(frozen=True)
class ScheduledTask:
    """Immutable description and state of schedulable AI work."""

    task_id: str
    tenant_id: str
    execution_id: str
    priority: int = 0
    execution_class: ProcessingMode = "standard"
    dependencies: tuple[str, ...] = ()
    deadline: datetime | None = None
    budget: TaskBudget = TaskBudget()
    status: TaskStatus = "queued"
    attempt: int = 0
    cancelled: bool = False

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.execution_id.strip():
            raise ValueError("execution_id is required")

        if not self.execution_class.strip():
            raise ValueError("execution_class is required")

        if self.execution_class not in _ALL_PROCESSING_MODES:
            raise ValueError(
                f"unsupported processing mode: {self.execution_class}"
            )

        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("duplicate task dependency detected")

        if any(not dependency.strip() for dependency in self.dependencies):
            raise ValueError("task dependency IDs are required")

        if self.attempt < 0:
            raise ValueError("attempt cannot be negative")

        if self.attempt > self.budget.max_attempts:
            raise ValueError("attempt exceeds max_attempts")

        if self.deadline is not None and self.deadline.tzinfo is None:
            raise ValueError("deadline must be timezone-aware")

    @property
    def processing_mode(self) -> ProcessingMode:
        """Canonical processing-mode name for request/runtime integrations."""
        return self.execution_class

    @property
    def request_blocking(self) -> bool:
        """Whether this task belongs on a request-blocking execution path."""
        return is_request_blocking_mode(self.execution_class)


class TaskScheduler:
    """Deterministic, provider-neutral scheduler for AI work."""

    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}

    def submit(self, task: ScheduledTask) -> ScheduledTask:
        if task.task_id in self._tasks:
            raise ValueError(f"task already registered: {task.task_id}")

        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> ScheduledTask:
        if not task_id.strip():
            raise ValueError("task_id is required")

        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"unknown task: {task_id}") from exc

    def cancel(self, task_id: str) -> ScheduledTask:
        task = self.get(task_id)

        if task.status in {"completed", "failed", "cancelled"}:
            raise ValueError("terminal task cannot be cancelled")

        cancelled = replace(
            task,
            status="cancelled",
            cancelled=True,
        )
        self._tasks[task_id] = cancelled
        return cancelled

    def retry(self, task_id: str) -> ScheduledTask:
        task = self.get(task_id)

        if task.status != "failed":
            raise ValueError("only failed tasks may be retried")

        if task.attempt + 1 >= task.budget.max_attempts:
            raise ValueError("task retry budget exhausted")

        retried = replace(
            task,
            status="queued",
            attempt=task.attempt + 1,
            cancelled=False,
        )
        self._tasks[task_id] = retried
        return retried

    def mark_running(self, task_id: str) -> ScheduledTask:
        task = self.get(task_id)

        if not self.is_eligible(task_id):
            raise ValueError("task is not eligible to run")

        running = replace(task, status="running")
        self._tasks[task_id] = running
        return running

    def mark_completed(self, task_id: str) -> ScheduledTask:
        task = self.get(task_id)

        if task.status != "running":
            raise ValueError("only running tasks may complete")

        completed = replace(task, status="completed")
        self._tasks[task_id] = completed
        return completed

    def mark_failed(self, task_id: str) -> ScheduledTask:
        task = self.get(task_id)

        if task.status != "running":
            raise ValueError("only running tasks may fail")

        failed = replace(task, status="failed")
        self._tasks[task_id] = failed
        return failed

    def is_eligible(
        self,
        task_id: str,
        now: datetime | None = None,
    ) -> bool:
        task = self.get(task_id)

        if task.status != "queued" or task.cancelled:
            return False

        current_time = now or datetime.now(timezone.utc)

        if task.deadline is not None and current_time > task.deadline:
            return False

        for dependency_id in task.dependencies:
            if dependency_id not in self._tasks:
                return False

            dependency = self._tasks[dependency_id]

            if dependency.tenant_id != task.tenant_id:
                return False

            if dependency.status != "completed":
                return False

        running_count = sum(
            1
            for candidate in self._tasks.values()
            if candidate.tenant_id == task.tenant_id
            and candidate.execution_id == task.execution_id
            and candidate.status == "running"
        )

        if running_count >= task.budget.concurrency_limit:
            return False

        return True

    def next_task(
        self,
        tenant_id: str,
        now: datetime | None = None,
    ) -> ScheduledTask | None:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        eligible = [
            task
            for task in self._tasks.values()
            if task.tenant_id == tenant_id
            and self.is_eligible(task.task_id, now=now)
        ]

        if not eligible:
            return None

        return min(
            eligible,
            key=lambda task: (
                -task.priority,
                task.deadline or datetime.max.replace(tzinfo=timezone.utc),
                task.task_id,
            ),
        )

    def list_tasks(
        self,
        tenant_id: str | None = None,
    ) -> tuple[ScheduledTask, ...]:
        if tenant_id is None:
            return tuple(self._tasks.values())

        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        return tuple(
            task
            for task in self._tasks.values()
            if task.tenant_id == tenant_id
        )


__all__ = [
    "ProcessingMode",
    "ScheduledTask",
    "TaskBudget",
    "TaskScheduler",
    "TaskStatus",
    "is_request_blocking_mode",
]
