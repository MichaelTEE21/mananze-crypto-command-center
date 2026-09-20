import pytest

from mananze_os.workforce_assignment_planner import WorkforceAssignmentPlanner
from mananze_os.workforce_registry import WorkforceRegistry
from mananze_os.workforce_role import WorkforceRole


def make_registry() -> WorkforceRegistry:
    registry = WorkforceRegistry()

    registry.register(
        WorkforceRole(
            role_id="sales.specialist",
            name="Sales Specialist",
            description="Convert qualified opportunities into customers.",
            capability_ids=("sales",),
            skill_ids=("sales:lead_qualification",),
        )
    )

    return registry


def test_assignment_planner_creates_assignment() -> None:
    planner = WorkforceAssignmentPlanner(make_registry())

    assignment = planner.assign(
        assignment_id="assignment:001",
        execution_id="execution:001",
        node_id="sales",
        role_id="sales.specialist",
    )

    assert assignment.assignment_id == "assignment:001"
    assert assignment.execution_id == "execution:001"
    assert assignment.node_id == "sales"
    assert assignment.role_id == "sales.specialist"


def test_assignment_planner_rejects_unknown_role() -> None:
    planner = WorkforceAssignmentPlanner(make_registry())

    with pytest.raises(
        KeyError,
        match="unknown workforce role: missing.role",
    ):
        planner.assign(
            assignment_id="assignment:001",
            execution_id="execution:001",
            node_id="sales",
            role_id="missing.role",
        )
