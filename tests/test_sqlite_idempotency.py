from __future__ import annotations

import threading

from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.task_scheduler import ScheduledTask


def make_task(store: SQLiteTaskStore):
    task = ScheduledTask(
        task_id="task-1",
        tenant_id="tenant-a",
        execution_id="exec-1",
    )
    store.save(task)
    return task


def test_operation_key_is_stable_across_attempts(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")

    first = store.operation_key(
        "tenant-a",
        "task-1",
        "exec-1",
        "send-invoice",
    )

    second = store.operation_key(
        "tenant-a",
        "task-1",
        "exec-1",
        "send-invoice",
    )

    assert first == second
    assert len(first) == 64


def test_operation_key_is_tenant_scoped(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")

    tenant_a = store.operation_key(
        "tenant-a",
        "task-1",
        "exec-1",
        "send-invoice",
    )

    tenant_b = store.operation_key(
        "tenant-b",
        "task-1",
        "exec-1",
        "send-invoice",
    )

    assert tenant_a != tenant_b


def test_only_one_worker_can_claim_operation(tmp_path):
    db = tmp_path / "tasks.db"

    store_a = SQLiteTaskStore(db)
    store_b = SQLiteTaskStore(db)

    make_task(store_a)

    operation_key = store_a.operation_key(
        "tenant-a",
        "task-1",
        "exec-1",
        "send-invoice",
    )

    barrier = threading.Barrier(2)
    results: list[bool] = []
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker(store: SQLiteTaskStore):
        try:
            barrier.wait()
            result = store.claim_operation(
                tenant_id="tenant-a",
                operation_key=operation_key,
                task_id="task-1",
                execution_id="exec-1",
            )
            with lock:
                results.append(result)
        except Exception as exc:
            with lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(store_a,)),
        threading.Thread(target=worker, args=(store_b,)),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []
    assert sorted(results) == [False, True]


def test_completed_operation_preserves_result_and_evidence(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    make_task(store)

    operation_key = store.operation_key(
        "tenant-a",
        "task-1",
        "exec-1",
        "send-invoice",
    )

    assert store.claim_operation(
        tenant_id="tenant-a",
        operation_key=operation_key,
        task_id="task-1",
        execution_id="exec-1",
        lease_id="lease-1",
    )

    record = store.complete_operation(
        tenant_id="tenant-a",
        operation_key=operation_key,
        lease_id="lease-1",
        result={"invoice_id": "INV-123"},
        evidence={"provider_status": "accepted"},
    )

    assert record["status"] == "completed"
    assert record["result_json"] == '{"invoice_id": "INV-123"}'
    assert record["evidence_json"] == '{"provider_status": "accepted"}'
    assert record["completed_at"] is not None


def test_completed_operation_cannot_be_claimed_again(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    make_task(store)

    operation_key = store.operation_key(
        "tenant-a",
        "task-1",
        "exec-1",
        "send-invoice",
    )

    assert store.claim_operation(
        tenant_id="tenant-a",
        operation_key=operation_key,
        task_id="task-1",
        execution_id="exec-1",
        lease_id="lease-1",
    )

    store.complete_operation(
        tenant_id="tenant-a",
        operation_key=operation_key,
        lease_id="lease-1",
        result={"invoice_id": "INV-123"},
    )

    assert not store.claim_operation(
        tenant_id="tenant-a",
        operation_key=operation_key,
        task_id="task-1",
        execution_id="exec-1",
    )


def test_idempotency_record_is_tenant_isolated(tmp_path):
    store = SQLiteTaskStore(tmp_path / "tasks.db")
    make_task(store)

    operation_key = store.operation_key(
        "tenant-a",
        "task-1",
        "exec-1",
        "send-invoice",
    )

    assert store.claim_operation(
        tenant_id="tenant-a",
        operation_key=operation_key,
        task_id="task-1",
        execution_id="exec-1",
        lease_id="lease-1",
    )

    assert (
        store.idempotency_record(
            tenant_id="tenant-a",
            operation_key=operation_key,
        )
        is not None
    )

    assert (
        store.idempotency_record(
            tenant_id="tenant-b",
            operation_key=operation_key,
        )
        is None
    )
