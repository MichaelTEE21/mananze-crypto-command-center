"""SQLite-backed durable task persistence for Mananze OS."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock


from mananze_os.task_recovery import TaskRecoveryRecord
from mananze_os.task_scheduler import ScheduledTask, TaskBudget


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class SQLiteTaskStore:
    """Durable task/recovery store backed by SQLite.

    Persistence owns task state, leases and recovery metadata.
    Policy, authorization, approval, execution lifecycle and
    verification remain authoritative elsewhere.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = RLock()

        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=FULL;

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    execution_class TEXT NOT NULL,
                    dependencies TEXT NOT NULL,
                    deadline TEXT,
                    max_attempts INTEGER NOT NULL,
                    time_budget_seconds REAL,
                    token_budget INTEGER,
                    cost_budget REAL,
                    concurrency_limit INTEGER,
                    status TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    cancelled INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS task_recovery (
                    task_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    lease_id TEXT,
                    started_at TEXT,
                    heartbeat_at TEXT,
                    completed_at TEXT,
                    recovery_count INTEGER NOT NULL,
                    last_recovery_reason TEXT,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                );

                CREATE TABLE IF NOT EXISTS task_idempotency (
                    tenant_id TEXT NOT NULL,
                    operation_key TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    lease_id TEXT,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    evidence_json TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    PRIMARY KEY (tenant_id, operation_key),
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_running
                    ON tasks(status, tenant_id, task_id);

                CREATE INDEX IF NOT EXISTS idx_recovery_heartbeat
                    ON task_recovery(heartbeat_at, started_at);
                """
            )

            try:
                conn.execute(
                    "ALTER TABLE task_idempotency ADD COLUMN lease_id TEXT"
                )
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.path,
            timeout=30.0,
            isolation_level="DEFERRED",
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    @staticmethod
    def _task_to_row(task: ScheduledTask) -> tuple:
        return (
            task.task_id,
            task.tenant_id,
            task.execution_id,
            task.priority,
            task.execution_class,
            json.dumps(list(task.dependencies)),
            _dt(task.deadline),
            task.budget.max_attempts,
            task.budget.time_budget_seconds,
            task.budget.token_budget,
            task.budget.cost_budget,
            task.budget.concurrency_limit,
            task.status,
            task.attempt,
            int(task.cancelled),
        )

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> ScheduledTask:
        return ScheduledTask(
            task_id=row["task_id"],
            tenant_id=row["tenant_id"],
            execution_id=row["execution_id"],
            priority=row["priority"],
            execution_class=row["execution_class"],
            dependencies=tuple(json.loads(row["dependencies"])),
            deadline=_parse_dt(row["deadline"]),
            budget=TaskBudget(
                max_attempts=row["max_attempts"],
                time_budget_seconds=row["time_budget_seconds"],
                token_budget=row["token_budget"],
                cost_budget=row["cost_budget"],
                concurrency_limit=row["concurrency_limit"],
            ),
            status=row["status"],
            attempt=row["attempt"],
            cancelled=bool(row["cancelled"]),
        )

    @staticmethod
    def _row_to_recovery(row: sqlite3.Row) -> TaskRecoveryRecord:
        return TaskRecoveryRecord(
            task_id=row["task_id"],
            tenant_id=row["tenant_id"],
            execution_id=row["execution_id"],
            lease_id=row["lease_id"],
            started_at=_parse_dt(row["started_at"]),
            heartbeat_at=_parse_dt(row["heartbeat_at"]),
            completed_at=_parse_dt(row["completed_at"]),
            recovery_count=row["recovery_count"],
            last_recovery_reason=row["last_recovery_reason"],
        )

    def save(self, task: ScheduledTask) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, tenant_id, execution_id, priority,
                    execution_class, dependencies, deadline,
                    max_attempts, time_budget_seconds, token_budget,
                    cost_budget, concurrency_limit, status,
                    attempt, cancelled
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._task_to_row(task),
            )

            conn.execute(
                """
                INSERT INTO task_recovery (
                    task_id, tenant_id, execution_id,
                    recovery_count
                )
                VALUES (?, ?, ?, 0)
                """,
                (
                    task.task_id,
                    task.tenant_id,
                    task.execution_id,
                ),
            )

    def get(self, task_id: str) -> ScheduledTask:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()

        if row is None:
            raise KeyError(task_id)

        return self._row_to_task(row)

    def recovery(self, task_id: str) -> TaskRecoveryRecord:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM task_recovery WHERE task_id = ?",
                (task_id,),
            ).fetchone()

        if row is None:
            raise KeyError(task_id)

        return self._row_to_recovery(row)

    def update(self, task: ScheduledTask) -> None:
        current = self.get(task.task_id)

        if current.tenant_id != task.tenant_id:
            raise PermissionError("tenant identity cannot change")

        if current.execution_id != task.execution_id:
            raise ValueError("execution identity cannot change")

        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET priority = ?,
                    execution_class = ?,
                    dependencies = ?,
                    deadline = ?,
                    max_attempts = ?,
                    time_budget_seconds = ?,
                    token_budget = ?,
                    cost_budget = ?,
                    concurrency_limit = ?,
                    status = ?,
                    attempt = ?,
                    cancelled = ?
                WHERE task_id = ?
                """,
                (
                    task.priority,
                    task.execution_class,
                    json.dumps(list(task.dependencies)),
                    _dt(task.deadline),
                    task.budget.max_attempts,
                    task.budget.time_budget_seconds,
                    task.budget.token_budget,
                    task.budget.cost_budget,
                    task.budget.concurrency_limit,
                    task.status,
                    task.attempt,
                    int(task.cancelled),
                    task.task_id,
                ),
            )

    def start(
        self,
        task_id: str,
        lease_id: str,
        now: datetime | None = None,
    ) -> ScheduledTask:
        now = now or datetime.now(timezone.utc)

        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE tasks
                SET status = 'running'
                WHERE task_id = ?
                  AND status = 'queued'
                """,
                (task_id,),
            )

            if cursor.rowcount == 0:
                raise ValueError("task is no longer queued")

            recovery_cursor = conn.execute(
                """
                UPDATE task_recovery
                SET lease_id = ?,
                    started_at = ?,
                    heartbeat_at = ?,
                    completed_at = NULL
                WHERE task_id = ?
                  AND lease_id IS NULL
                """,
                (
                    lease_id,
                    _dt(now),
                    _dt(now),
                    task_id,
                ),
            )

            if recovery_cursor.rowcount == 0:
                conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'queued'
                    WHERE task_id = ?
                      AND status = 'running'
                    """,
                    (task_id,),
                )
                raise ValueError("task lease is already owned")

        return self.get(task_id)

    def heartbeat(
        self,
        task_id: str,
        lease_id: str,
        now: datetime | None = None,
    ) -> ScheduledTask:
        now = now or datetime.now(timezone.utc)

        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE task_recovery
                SET heartbeat_at = ?
                WHERE task_id = ?
                  AND lease_id = ?
                """,
                (
                    _dt(now),
                    task_id,
                    lease_id,
                ),
            )

            if cursor.rowcount == 0:
                raise PermissionError("invalid task lease")

            status = conn.execute(
                """
                SELECT status
                FROM tasks
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()

            if status is None:
                raise KeyError(task_id)

            if status["status"] != "running":
                raise ValueError(
                    "only running tasks can heartbeat"
                )

        return self.get(task_id)

    def complete(
        self,
        task_id: str,
        lease_id: str,
        now: datetime | None = None,
    ) -> ScheduledTask:
        now = now or datetime.now(timezone.utc)

        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE tasks
                SET status = 'completed'
                WHERE task_id = ?
                  AND status = 'running'
                  AND EXISTS (
                      SELECT 1
                      FROM task_recovery
                      WHERE task_id = ?
                        AND lease_id = ?
                  )
                """,
                (
                    task_id,
                    task_id,
                    lease_id,
                ),
            )

            if cursor.rowcount == 0:
                raise PermissionError(
                    "task is not running under the supplied lease"
                )

            conn.execute(
                """
                UPDATE task_recovery
                SET completed_at = ?,
                    heartbeat_at = ?,
                    lease_id = NULL
                WHERE task_id = ?
                  AND lease_id = ?
                """,
                (
                    _dt(now),
                    _dt(now),
                    task_id,
                    lease_id,
                ),
            )

        return self.get(task_id)

    def list_tasks(
        self,
        tenant_id: str | None = None,
    ) -> list[ScheduledTask]:
        with self._lock, self._connect() as conn:
            if tenant_id is None:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM tasks
                    ORDER BY task_id
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM tasks
                    WHERE tenant_id = ?
                    ORDER BY task_id
                    """,
                    (tenant_id,),
                ).fetchall()

        return [self._row_to_task(row) for row in rows]

    def stale_running_tasks(
        self,
        stale_after,
        now: datetime | None = None,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[ScheduledTask]:
        if limit < 1:
            raise ValueError("limit must be >= 1")

        now = now or datetime.now(timezone.utc)
        cutoff = now - stale_after

        with self._lock, self._connect() as conn:
            query = """
                SELECT t.*
                FROM tasks t
                JOIN task_recovery r
                  ON r.task_id = t.task_id
                WHERE t.status = 'running'
                  AND COALESCE(
                      r.heartbeat_at,
                      r.started_at
                  ) <= ?
            """

            params: list[object] = [_dt(cutoff)]

            if tenant_id is not None:
                query += " AND t.tenant_id = ?"
                params.append(tenant_id)

            query += """
                ORDER BY COALESCE(
                    r.heartbeat_at,
                    r.started_at
                ), t.task_id
                LIMIT ?
            """
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

        return [self._row_to_task(row) for row in rows]

    def recover(
        self,
        task_id: str,
        stale_after,
        now: datetime | None = None,
    ) -> ScheduledTask:
        now = now or datetime.now(timezone.utc)

        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    t.*,
                    r.lease_id,
                    r.started_at,
                    r.heartbeat_at,
                    r.recovery_count
                FROM tasks t
                JOIN task_recovery r
                  ON r.task_id = t.task_id
                WHERE t.task_id = ?
                """,
                (task_id,),
            ).fetchone()

            if row is None:
                raise KeyError(task_id)

            if row["status"] in {"completed", "cancelled"}:
                return self._row_to_task(row)

            if row["status"] != "running":
                return self._row_to_task(row)

            last_heartbeat = (
                _parse_dt(row["heartbeat_at"])
                or _parse_dt(row["started_at"])
            )

            if last_heartbeat is None:
                raise ValueError(
                    "running task has no lease timestamp"
                )

            if now - last_heartbeat < stale_after:
                return self._row_to_task(row)

            lease_id = row["lease_id"]
            attempt = row["attempt"]
            max_attempts = row["max_attempts"]

            if attempt + 1 >= max_attempts:
                cursor = conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'failed'
                    WHERE task_id = ?
                      AND status = 'running'
                      AND attempt = ?
                      AND EXISTS (
                          SELECT 1
                          FROM task_recovery
                          WHERE task_id = ?
                            AND lease_id IS ?
                      )
                    """,
                    (
                        task_id,
                        attempt,
                        task_id,
                        lease_id,
                    ),
                )

                if cursor.rowcount == 0:
                    current = conn.execute(
                        "SELECT * FROM tasks WHERE task_id = ?",
                        (task_id,),
                    ).fetchone()
                    return self._row_to_task(current)

                conn.execute(
                    """
                    UPDATE task_recovery
                    SET lease_id = NULL,
                        last_recovery_reason = ?
                    WHERE task_id = ?
                      AND lease_id IS ?
                    """,
                    (
                        "stale execution lease; retry budget exhausted",
                        task_id,
                        lease_id,
                    ),
                )

            else:
                cursor = conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'queued',
                        attempt = attempt + 1,
                        cancelled = 0
                    WHERE task_id = ?
                      AND status = 'running'
                      AND attempt = ?
                      AND EXISTS (
                          SELECT 1
                          FROM task_recovery
                          WHERE task_id = ?
                            AND lease_id IS ?
                      )
                    """,
                    (
                        task_id,
                        attempt,
                        task_id,
                        lease_id,
                    ),
                )

                if cursor.rowcount == 0:
                    current = conn.execute(
                        "SELECT * FROM tasks WHERE task_id = ?",
                        (task_id,),
                    ).fetchone()
                    return self._row_to_task(current)

                conn.execute(
                    """
                    UPDATE task_recovery
                    SET lease_id = NULL,
                        started_at = NULL,
                        heartbeat_at = NULL,
                        recovery_count = recovery_count + 1,
                        last_recovery_reason = ?
                    WHERE task_id = ?
                      AND lease_id IS ?
                    """,
                    (
                        "stale execution lease",
                        task_id,
                        lease_id,
                    ),
                )

            final_row = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()

        return self._row_to_task(final_row)

    @staticmethod
    def idempotency_key(
        tenant_id: str,
        task_id: str,
        execution_id: str,
        attempt: int,
    ) -> str:
        return hashlib.sha256(
            f"{tenant_id}|{task_id}|{execution_id}|{attempt}".encode()
        ).hexdigest()



    @staticmethod
    def operation_key(
        tenant_id: str,
        task_id: str,
        execution_id: str,
        operation: str,
    ) -> str:
        """Return a stable identity for one protected logical operation."""
        if not tenant_id.strip():
            raise ValueError("tenant_id cannot be blank")
        if not task_id.strip():
            raise ValueError("task_id cannot be blank")
        if not execution_id.strip():
            raise ValueError("execution_id cannot be blank")
        if not operation.strip():
            raise ValueError("operation cannot be blank")

        return hashlib.sha256(
            f"{tenant_id}|{task_id}|{execution_id}|{operation}".encode()
        ).hexdigest()

    def claim_operation(
        self,
        *,
        tenant_id: str,
        operation_key: str,
        task_id: str,
        execution_id: str,
        lease_id: str | None = None,
        now: datetime | None = None,
    ) -> bool:
        """Atomically claim a protected logical operation."""

        if not tenant_id.strip():
            raise ValueError("tenant_id cannot be blank")
        if not operation_key.strip():
            raise ValueError("operation_key cannot be blank")
        if not task_id.strip():
            raise ValueError("task_id cannot be blank")
        if not execution_id.strip():
            raise ValueError("execution_id cannot be blank")

        timestamp = _dt(now or datetime.now(timezone.utc))

        with self._lock, self._connect() as conn:
            task_row = conn.execute(
                """
                SELECT tenant_id, execution_id
                FROM tasks
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()

            if task_row is None:
                raise KeyError("task does not exist")

            if (
                task_row["tenant_id"] != tenant_id
                or task_row["execution_id"] != execution_id
            ):
                raise ValueError(
                    "task execution context does not match idempotency claim"
                )

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO task_idempotency (
                    tenant_id,
                    operation_key,
                    task_id,
                    execution_id,
                    lease_id,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, 'in_progress', ?)
                """,
                (
                    tenant_id,
                    operation_key,
                    task_id,
                    execution_id,
                    lease_id,
                    timestamp,
                ),
            )

            if cursor.rowcount == 1:
                return True

            existing = conn.execute(
                """
                SELECT lease_id, status
                FROM task_idempotency
                WHERE tenant_id = ?
                  AND operation_key = ?
                """,
                (tenant_id, operation_key),
            ).fetchone()

            if existing is None:
                raise RuntimeError(
                    "idempotency claim was lost without a durable record"
                )

            if existing["status"] == "completed":
                return False

            if existing["status"] != "in_progress":
                return False

            recovery = conn.execute(
                """
                SELECT lease_id
                FROM task_recovery
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()

            current_lease = (
                recovery["lease_id"] if recovery is not None else None
            )

            # The durable task store has already accepted this lease.
            # Allow the current execution owner to take ownership of the
            # same logical operation if the previous operation lease is
            # absent or belongs to an obsolete worker.
            if (
                lease_id is not None
                and current_lease == lease_id
                and existing["lease_id"] != lease_id
            ):
                reclaimed = conn.execute(
                    """
                    UPDATE task_idempotency
                    SET lease_id = ?
                    WHERE tenant_id = ?
                      AND operation_key = ?
                      AND status = 'in_progress'
                      AND (
                          lease_id IS NULL
                          OR lease_id != ?
                      )
                    """,
                    (
                        lease_id,
                        tenant_id,
                        operation_key,
                        lease_id,
                    ),
                )

                return reclaimed.rowcount == 1

            return False

    def idempotency_record(
        self,
        *,
        tenant_id: str,
        operation_key: str,
    ) -> dict | None:
        """Return the durable operation record for a tenant."""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM task_idempotency
                WHERE tenant_id = ?
                  AND operation_key = ?
                """,
                (tenant_id, operation_key),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def complete_operation(
        self,
        *,
        tenant_id: str,
        operation_key: str,
        lease_id: str,
        result: object | None = None,
        evidence: object | None = None,
        now: datetime | None = None,
    ) -> dict:
        """Durably complete a logical operation owned by the supplied lease."""
        if not tenant_id.strip():
            raise ValueError("tenant_id cannot be blank")
        if not operation_key.strip():
            raise ValueError("operation_key cannot be blank")
        if not lease_id.strip():
            raise ValueError("lease_id cannot be blank")

        timestamp = _dt(now or datetime.now(timezone.utc))

        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE task_idempotency
                SET status = 'completed',
                    result_json = ?,
                    evidence_json = ?,
                    completed_at = ?
                WHERE tenant_id = ?
                  AND operation_key = ?
                  AND lease_id = ?
                  AND status = 'in_progress'
                """,
                (
                    json.dumps(result),
                    json.dumps(evidence),
                    timestamp,
                    tenant_id,
                    operation_key,
                    lease_id,
                ),
            )

            if cursor.rowcount != 1:
                raise PermissionError(
                    "operation is not in progress under the supplied lease"
                )

            row = conn.execute(
                """
                SELECT *
                FROM task_idempotency
                WHERE tenant_id = ?
                  AND operation_key = ?
                """,
                (tenant_id, operation_key),
            ).fetchone()

        return dict(row)

__all__ = ["SQLiteTaskStore"]
