from dataclasses import replace

import pytest

from mananze_os.compiler import IntelligenceCompiler
from mananze_os.execution_context_integrity import ExecutionContextIntegrity
from mananze_os.work_order import WorkOrder
from mananze_os.workforce_planner import WorkforcePlanner


def make_context():
    work_order = WorkOrder(
        work_order_id="wo:test-001",
        tenant_id="tenant-a",
        objective="Improve logistics delivery operations",
    )

    compiler = IntelligenceCompiler()
    plan = compiler.compile(work_order)

    workforce = WorkforcePlanner().plan_from_requirements(
        work_order.work_order_id,
        plan.objective,
        plan.requirements,
    )

    return work_order, plan, workforce


def test_binds_valid_execution_context():
    work_order, plan, workforce = make_context()

    context = ExecutionContextIntegrity().bind(
        work_order=work_order,
        plan=plan,
        workforce=workforce,
        execution_id="exec:wo:test-001",
        task_id="task:wo:test-001",
    )

    assert context.work_order_id == "wo:test-001"
    assert context.tenant_id == "tenant-a"
    assert context.execution_id == "exec:wo:test-001"
    assert context.task_id == "task:wo:test-001"


def test_rejects_plan_from_different_work_order():
    work_order, plan, workforce = make_context()

    invalid_plan = replace(plan, work_order_id="wo:other")

    with pytest.raises(ValueError, match="work_order_id"):
        ExecutionContextIntegrity().bind(
            work_order,
            invalid_plan,
            workforce,
            "exec:wo:test-001",
            "task:wo:test-001",
        )


def test_rejects_workforce_from_different_work_order():
    work_order, plan, workforce = make_context()

    invalid_workforce = replace(workforce, work_order_id="wo:other")

    with pytest.raises(ValueError, match="work_order_id"):
        ExecutionContextIntegrity().bind(
            work_order,
            plan,
            invalid_workforce,
            "exec:wo:test-001",
            "task:wo:test-001",
        )


def test_rejects_objective_mismatch():
    work_order, plan, workforce = make_context()

    invalid_plan = replace(
        plan,
        objective="Unrelated objective",
    )

    with pytest.raises(ValueError, match="objective"):
        ExecutionContextIntegrity().bind(
            work_order,
            invalid_plan,
            workforce,
            "exec:wo:test-001",
            "task:wo:test-001",
        )


def test_rejects_cross_tenant_plan():
    work_order, plan, workforce = make_context()

    invalid_plan = replace(plan, tenant_id="tenant-b")

    with pytest.raises(PermissionError, match="tenant"):
        ExecutionContextIntegrity().bind(
            work_order,
            invalid_plan,
            workforce,
            "exec:wo:test-001",
            "task:wo:test-001",
        )


def test_rejects_wrong_execution_id():
    work_order, plan, workforce = make_context()

    with pytest.raises(ValueError, match="execution_id"):
        ExecutionContextIntegrity().bind(
            work_order,
            plan,
            workforce,
            "exec:wrong",
            "task:wo:test-001",
        )


def test_rejects_wrong_task_id():
    work_order, plan, workforce = make_context()

    with pytest.raises(ValueError, match="task_id"):
        ExecutionContextIntegrity().bind(
            work_order,
            plan,
            workforce,
            "exec:wo:test-001",
            "task:wrong",
        )


def test_rejects_missing_compiled_capability():
    work_order, plan, workforce = make_context()

    invalid_workforce = replace(
        workforce,
        roles=workforce.roles[:-1],
    )

    with pytest.raises(ValueError, match="missing compiled capabilities"):
        ExecutionContextIntegrity().bind(
            work_order,
            plan,
            invalid_workforce,
            "exec:wo:test-001",
            "task:wo:test-001",
        )


def test_rejects_uncompiled_capability():
    work_order, plan, workforce = make_context()

    extra_role = replace(
        workforce.roles[0],
        role_id="uncompiled",
        capability_id="uncompiled",
    )

    invalid_workforce = replace(
        workforce,
        roles=workforce.roles + (extra_role,),
    )

    with pytest.raises(ValueError, match="uncompiled capabilities"):
        ExecutionContextIntegrity().bind(
            work_order,
            plan,
            invalid_workforce,
            "exec:wo:test-001",
            "task:wo:test-001",
        )
