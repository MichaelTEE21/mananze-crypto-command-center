from __future__ import annotations

from mananze_os.sqlite_task_store import SQLiteTaskStore

from tests.test_runtime_durable_execution import (
    build_request,
    build_runtime,
)


def test_runtime_persists_completed_idempotency_operation(tmp_path):
    db = tmp_path / "tasks.db"
    runtime = build_runtime(db)

    prepared = runtime.prepare(
        build_request("req-idempotency-runtime")
    )

    result = runtime.execute(
        prepared,
        approved_by="human:tshepo",
    )

    task_id = "task:req-idempotency-runtime"
    execution_id = result.execution_state.execution_id

    store = SQLiteTaskStore(db)

    operation_key = store.operation_key(
        "dentist-demo",
        task_id,
        execution_id,
        "controlled-execution",
    )

    record = store.idempotency_record(
        tenant_id="dentist-demo",
        operation_key=operation_key,
    )

    assert record is not None
    assert record["status"] == "completed"
    assert record["completed_at"] is not None


def test_runtime_does_not_execute_completed_operation_twice(tmp_path):
    db = tmp_path / "tasks.db"
    runtime = build_runtime(db)

    prepared = runtime.prepare(
        build_request("req-idempotency-no-double")
    )

    first = runtime.execute(
        prepared,
        approved_by="human:tshepo",
    )

    task_id = "task:req-idempotency-no-double"
    execution_id = first.execution_state.execution_id

    store = SQLiteTaskStore(db)

    operation_key = store.operation_key(
        "dentist-demo",
        task_id,
        execution_id,
        "controlled-execution",
    )

    record_before = store.idempotency_record(
        tenant_id="dentist-demo",
        operation_key=operation_key,
    )

    assert record_before is not None
    assert record_before["status"] == "completed"

    try:
        runtime.execute(
            prepared,
            approved_by="human:tshepo",
        )
    except (ValueError, PermissionError, RuntimeError):
        pass

    record_after = store.idempotency_record(
        tenant_id="dentist-demo",
        operation_key=operation_key,
    )

    assert record_after is not None
    assert record_after["status"] == "completed"
    assert record_after["completed_at"] == record_before["completed_at"]
