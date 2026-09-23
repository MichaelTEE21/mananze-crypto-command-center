"""Durable task state and crash-recovery foundation for Mananze OS."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from threading import RLock

from mananze_os.task_scheduler import ScheduledTask


@dataclass(frozen=True)
class TaskRecoveryRecord:
    """Recovery metadata associated with one scheduled task."""

    task_id: str
    tenant_id: str
    execution_id: str
    lease_id: str | None = None
    started_at: datetime | None = None
    heartbeat_at: datetime | None = None
    completed_at: datetime | None = None
    recovery_count: int = 0
    last_recovery_reason: str | None = None

    def __post_init__(self) -> None:
        for name in ("task_id", "tenant_id", "execution_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")

        for name in ("started_at", "heartbeat_at", "completed_at"):
            value = getattr(self, name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")

        if self.recovery_count < 0:
            raise ValueError("recovery_count cannot be negative")


class DurableTaskStore:
    """Thread-safe provider-neutral durable task state abstraction.

    This foundation intentionally keeps persistence behind a small contract.
    A production deployment can replace the backing implementation with
    SQLite/PostgreSQL/etc. without changing scheduler semantics.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}
        self._recovery: dict[str, TaskRecoveryRecord] = {}
        self._lock = RLock()

    def save(self, task: ScheduledTask) -> ScheduledTask:
        with self._lock:
            existing = self._tasks.get(task.task_id)
            if existing is not None:
                raise ValueError(f"task already registered: {task.task_id}")

            self._tasks[task.task_id] = task
            self._recovery[task.task_id] = TaskRecoveryRecord(
                task_id=task.task_id,
                tenant_id=task.tenant_id,
                execution_id=task.execution_id,
            )
            return task

    def get(self, task_id: str) -> ScheduledTask:
        if not task_id.strip():
            raise ValueError("task_id is required")

        with self._lock:
            try:
                return self._tasks[task_id]
            except KeyError as exc:
                raise KeyError(f"unknown task: {task_id}") from exc

    def recovery(self, task_id: str) -> TaskRecoveryRecord:
        if not task_id.strip():
            raise ValueError("task_id is required")

        with self._lock:
            try:
                return self._recovery[task_id]
            except KeyError as exc:
                raise KeyError(f"unknown task: {task_id}") from exc

    def update(self, task: ScheduledTask) -> ScheduledTask:
        with self._lock:
            existing = self._tasks.get(task.task_id)
            if existing is None:
                raise KeyError(f"unknown task: {task.task_id}")

            if existing.tenant_id != task.tenant_id:
                raise PermissionError("task tenant cannot change")

            if existing.execution_id != task.execution_id:
                raise ValueError("task execution_id cannot change")

            self._tasks[task.task_id] = task
            return task

    def start(
        self,
        task_id: str,
        lease_id: str,
        now: datetime | None = None,
    ) -> ScheduledTask:
        if not lease_id.strip():
            raise ValueError("lease_id is required")

        current = now or datetime.now(timezone.utc)

        with self._lock:
            task = self.get(task_id)

            if task.status != "queued":
                raise ValueError("only queued tasks may start")

            started = replace(task, status="running")
            self._tasks[task_id] = started

            record = self._recovery[task_id]
            self._recovery[task_id] = replace(
                record,
                lease_id=lease_id,
                started_at=current,
                heartbeat_at=current,
                completed_at=None,
            )
            return started

    def heartbeat(
        self,
        task_id: str,
        lease_id: str,
        now: datetime | None = None,
    ) -> ScheduledTask:
        current = now or datetime.now(timezone.utc)

        with self._lock:
            task = self.get(task_id)
            record = self._recovery[task_id]

            if task.status != "running":
                raise ValueError("only running tasks may heartbeat")

            if record.lease_id != lease_id:
                raise PermissionError("invalid task lease")

            self._recovery[task_id] = replace(
                record,
                heartbeat_at=current,
            )
            return task

    def complete(
        self,
        task_id: str,
        lease_id: str,
        now: datetime | None = None,
    ) -> ScheduledTask:
        current = now or datetime.now(timezone.utc)

        with self._lock:
            task = self.get(task_id)
            record = self._recovery[task_id]

            if task.status != "running":
                raise ValueError("only running tasks may complete")

            if record.lease_id != lease_id:
                raise PermissionError("invalid task lease")

            completed = replace(task, status="completed")
            self._tasks[task_id] = completed
            self._recovery[task_id] = replace(
                record,
                heartbeat_at=current,
                completed_at=current,
            )
            return completed

    def list_tasks(
        self,
        tenant_id: str | None = None,
    ) -> tuple[ScheduledTask, ...]:
        with self._lock:
            tasks = tuple(self._tasks.values())

        if tenant_id is None:
            return tasks

        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        return tuple(
            task
            for task in tasks
            if task.tenant_id == tenant_id
        )

    def stale_running_tasks(
        self,
        stale_after: timedelta,
        now: datetime | None = None,
        tenant_id: str | None = None,
    ) -> tuple[ScheduledTask, ...]:
        if stale_after <= timedelta(0):
            raise ValueError("stale_after must be positive")

        current = now or datetime.now(timezone.utc)

        with self._lock:
            candidates = tuple(self._tasks.values())

        stale: list[ScheduledTask] = []

        for task in candidates:
            if task.status != "running":
                continue

            if tenant_id is not None and task.tenant_id != tenant_id:
                continue

            record = self.recovery(task.task_id)
            heartbeat = record.heartbeat_at or record.started_at

            if heartbeat is None:
                stale.append(task)
                continue

            if current - heartbeat >= stale_after:
                stale.append(task)

        return tuple(stale)

    def recover(
        self,
        task_id: str,
        stale_after: timedelta,
        now: datetime | None = None,
    ) -> ScheduledTask:
        current = now or datetime.now(timezone.utc)

        with self._lock:
            task = self.get(task_id)
            record = self.recovery(task_id)

            if task.status == "completed":
                return task

            if task.status == "cancelled":
                return task

            if task.status != "running":
                return task

            heartbeat = record.heartbeat_at or record.started_at

            if heartbeat is not None and current - heartbeat < stale_after:
                raise ValueError("task lease is still active")

            if task.attempt + 1 >= task.budget.max_attempts:
                failed = replace(task, status="failed")
                self._tasks[task_id] = failed
                self._recovery[task_id] = replace(
                    record,
                    recovery_count=record.recovery_count + 1,
                    last_recovery_reason="stale lease exhausted retry budget",
                )
                return failed

            recovered = replace(
                task,
                status="queued",
                attempt=task.attempt + 1,
                cancelled=False,
            )

            self._tasks[task_id] = recovered
            self._recovery[task_id] = replace(
                record,
                lease_id=None,
                heartbeat_at=None,
                recovery_count=record.recovery_count + 1,
                last_recovery_reason="stale execution lease after interruption",
            )
            return recovered

    @staticmethod
    def idempotency_key(
        task_id: str,
        execution_id: str,
        attempt: int,
    ) -> str:
        if not task_id.strip():
            raise ValueError("task_id is required")

        if not execution_id.strip():
            raise ValueError("execution_id is required")

        if attempt < 0:
            raise ValueError("attempt cannot be negative")

        material = f"{task_id}|{execution_id}|{attempt}".encode("utf-8")
        return sha256(material).hexdigest()


__all__ = [
    "DurableTaskStore",
    "TaskRecoveryRecord",
]
