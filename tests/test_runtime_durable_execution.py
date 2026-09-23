from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from mananze_os.authority import Authority
from mananze_os.input_request import InputRequest
from mananze_os.permission import CapabilityPermission
from mananze_os.runtime import MananzeRuntime
from mananze_os.sqlite_task_store import SQLiteTaskStore
from mananze_os.tenant import Tenant


CAPABILITIES = (
    "marketing",
    "lead_generation",
    "sales",
    "appointment_booking",
    "customer_communications",
    "retention",
    "revenue",
    "reporting",
    "operations",
)


def build_runtime(db_path: Path) -> MananzeRuntime:
    authorities = (
        Authority(
            actor_id="human:tshepo",
            level="human",
            can_execute=True,
            requires_approval=True,
        ),
        Authority(
            actor_id="human:charmaine",
            level="human",
            can_execute=True,
            requires_approval=True,
        ),
    )

    permissions = tuple(
        CapabilityPermission(
            actor_id=actor_id,
            tenant_id="dentist-demo",
            capability_id=capability_id,
        )
        for actor_id in (
            "human:tshepo",
            "human:charmaine",
        )
        for capability_id in CAPABILITIES
    )

    return MananzeRuntime(
        tenants=(
            Tenant(
                tenant_id="dentist-demo",
                name="Dentist Demo",
            ),
        ),
        authorities=authorities,
        permissions=permissions,
        task_store=SQLiteTaskStore(db_path),
    )


def build_request(
    request_id: str,
    actor_id: str = "human:tshepo",
) -> InputRequest:
    return InputRequest(
        request_id=request_id,
        tenant_id="dentist-demo",
        actor_id=actor_id,
        objective="Increase dental practice patient bookings",
    )


def test_prepare_persists_task(tmp_path):
    runtime = build_runtime(tmp_path / "tasks.db")

    prepared = runtime.prepare(
        build_request("req-persist")
    )

    task = runtime.task_store.get(
        f"task:{prepared.work_order.work_order_id}"
    )

    assert task is not None
    assert task.status == "queued"
    assert task.tenant_id == "dentist-demo"
    assert task.execution_id == prepared.execution_state.execution_id


def test_prepare_does_not_acquire_execution_lease(tmp_path):
    runtime = build_runtime(tmp_path / "tasks.db")

    prepared = runtime.prepare(
        build_request("req-no-lease")
    )

    task_id = f"task:{prepared.work_order.work_order_id}"
    recovery = runtime.task_store.recovery(task_id)

    assert recovery.lease_id is None
    assert recovery.started_at is None
    assert recovery.heartbeat_at is None


def test_tshepo_can_approve_and_complete(tmp_path):
    runtime = build_runtime(tmp_path / "tasks.db")

    prepared = runtime.prepare(
        build_request("req-tshepo")
    )

    result = runtime.execute(
        prepared,
        approved_by="human:tshepo",
    )

    task_id = f"task:{prepared.work_order.work_order_id}"
    task = runtime.task_store.get(task_id)
    recovery = runtime.task_store.recovery(task_id)

    assert result.execution_state.status == "completed"
    assert task is not None
    assert task.status == "completed"
    assert recovery.completed_at is not None
    assert recovery.lease_id is None


def test_charmaine_can_approve_and_complete(tmp_path):
    runtime = build_runtime(tmp_path / "tasks.db")

    prepared = runtime.prepare(
        build_request(
            "req-charmaine",
            actor_id="human:charmaine",
        )
    )

    result = runtime.execute(
        prepared,
        approved_by="human:charmaine",
    )

    task_id = f"task:{prepared.work_order.work_order_id}"
    task = runtime.task_store.get(task_id)

    assert result.execution_state.status == "completed"
    assert task is not None
    assert task.status == "completed"


def test_unrecognized_approver_is_rejected(tmp_path):
    runtime = build_runtime(tmp_path / "tasks.db")

    prepared = runtime.prepare(
        build_request("req-invalid-approver")
    )

    with pytest.raises(PermissionError):
        runtime.execute(
            prepared,
            approved_by="human:unknown",
        )

    task_id = f"task:{prepared.work_order.work_order_id}"
    task = runtime.task_store.get(task_id)

    assert task is not None
    assert task.status == "queued"

    recovery = runtime.task_store.recovery(task_id)
    assert recovery.lease_id is None


def test_completed_task_cannot_be_executed_again(tmp_path):
    runtime = build_runtime(tmp_path / "tasks.db")

    prepared = runtime.prepare(
        build_request("req-no-double-execution")
    )

    first = runtime.execute(
        prepared,
        approved_by="human:tshepo",
    )

    assert first.execution_state.status == "completed"

    with pytest.raises(ValueError):
        runtime.execute(
            prepared,
            approved_by="human:tshepo",
        )

    task_id = f"task:{prepared.work_order.work_order_id}"
    task = runtime.task_store.get(task_id)

    assert task is not None
    assert task.status == "completed"
    assert task.attempt == 0


def test_durable_state_survives_runtime_restart(tmp_path):
    db_path = tmp_path / "tasks.db"

    runtime_one = build_runtime(db_path)

    prepared = runtime_one.prepare(
        build_request("req-restart")
    )

    task_id = f"task:{prepared.work_order.work_order_id}"

    assert runtime_one.task_store.get(task_id) is not None

    runtime_two = build_runtime(db_path)

    persisted = runtime_two.task_store.get(task_id)

    assert persisted is not None
    assert persisted.status == "queued"
    assert persisted.execution_id == prepared.execution_state.execution_id


def test_different_tenants_remain_isolated(tmp_path):
    db_path = tmp_path / "tasks.db"
    store = SQLiteTaskStore(db_path)

    from mananze_os.task_scheduler import ScheduledTask

    store.save(
        ScheduledTask(
            task_id="tenant-a-task",
            tenant_id="tenant-a",
            execution_id="exec-a",
        )
    )

    store.save(
        ScheduledTask(
            task_id="tenant-b-task",
            tenant_id="tenant-b",
            execution_id="exec-b",
        )
    )

    tenant_a = store.list_tasks("tenant-a")
    tenant_b = store.list_tasks("tenant-b")

    assert [task.task_id for task in tenant_a] == ["tenant-a-task"]
    assert [task.task_id for task in tenant_b] == ["tenant-b-task"]


def test_execution_context_identity_matches_persisted_task(tmp_path):
    runtime = build_runtime(tmp_path / "tasks.db")

    prepared = runtime.prepare(
        build_request("req-context")
    )

    task_id = f"task:{prepared.work_order.work_order_id}"
    persisted = runtime.task_store.get(task_id)

    assert persisted is not None
    assert persisted.execution_id == prepared.execution_state.execution_id
    assert persisted.tenant_id == prepared.work_order.tenant_id


def test_prepare_still_requires_approval(tmp_path):
    runtime = build_runtime(tmp_path / "tasks.db")

    prepared = runtime.prepare(
        build_request("req-approval-boundary")
    )

    assert prepared.execution_state.status == "pending_approval"
    assert prepared.approval.status == "pending"

    task_id = f"task:{prepared.work_order.work_order_id}"
    recovery = runtime.task_store.recovery(task_id)

    assert recovery.lease_id is None
