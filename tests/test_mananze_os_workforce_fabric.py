import pytest

from mananze_os.workforce_assignment import WorkforceAssignment
from mananze_os.workforce_fabric import WorkforceFabric
from mananze_os.workforce_role import WorkforceRole


def make_role(role_id: str = "role-1") -> WorkforceRole:
    return WorkforceRole(
        role_id=role_id,
        name="Execution Operator",
        description="Coordinates controlled execution work.",
        capability_ids=("execution",),
        skill_ids=("execution:coordination",),
    )


def test_fabric_registers_and_retrieves_role() -> None:
    fabric = WorkforceFabric()
    role = make_role()

    fabric.register_role(role)

    assert fabric.get_role("role-1") == role


def test_fabric_lists_registered_roles() -> None:
    fabric = WorkforceFabric()
    role_one = make_role("role-1")
    role_two = make_role("role-2")

    fabric.register_role(role_one)
    fabric.register_role(role_two)

    assert fabric.list_roles() == (role_one, role_two)


def test_fabric_assigns_registered_role() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role())

    assignment = fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node_id="node-1",
        role_id="role-1",
    )

    assert isinstance(assignment, WorkforceAssignment)
    assert assignment.assignment_id == "assignment-1"
    assert assignment.execution_id == "execution-1"
    assert assignment.node_id == "node-1"
    assert assignment.role_id == "role-1"


def test_fabric_rejects_unknown_role_assignment() -> None:
    fabric = WorkforceFabric()

    with pytest.raises((KeyError, ValueError)):
        fabric.assign_role(
            assignment_id="assignment-1",
            execution_id="execution-1",
            node_id="node-1",
            role_id="missing-role",
        )
