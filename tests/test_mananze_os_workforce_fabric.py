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

    with pytest.raises(KeyError):
        fabric.assign_role(
            assignment_id="assignment-1",
            execution_id="execution-1",
            node_id="node-1",
            role_id="missing-role",
        )


def test_fabric_retrieves_assignment() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role())

    assignment = fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node_id="node-1",
        role_id="role-1",
    )

    assert fabric.get_assignment("assignment-1") == assignment


def test_fabric_lists_assignments() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role("role-1"))
    fabric.register_role(make_role("role-2"))

    assignment_one = fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node_id="node-1",
        role_id="role-1",
    )
    assignment_two = fabric.assign_role(
        assignment_id="assignment-2",
        execution_id="execution-1",
        node_id="node-2",
        role_id="role-2",
    )

    assert fabric.list_assignments() == (
        assignment_one,
        assignment_two,
    )


def test_fabric_rejects_duplicate_assignment() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role())

    fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node_id="node-1",
        role_id="role-1",
    )

    with pytest.raises(
        ValueError,
        match="assignment already exists: assignment-1",
    ):
        fabric.assign_role(
            assignment_id="assignment-1",
            execution_id="execution-2",
            node_id="node-2",
            role_id="role-1",
        )


def test_fabric_rejects_unknown_assignment_lookup() -> None:
    fabric = WorkforceFabric()

    with pytest.raises(
        KeyError,
        match="unknown workforce assignment: missing-assignment",
    ):
        fabric.get_assignment("missing-assignment")


def test_fabric_assignment_list_is_immutable_snapshot() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role())

    assignment = fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node_id="node-1",
        role_id="role-1",
    )

    assignments = fabric.list_assignments()

    assert isinstance(assignments, tuple)
    assert assignments == (assignment,)

    with pytest.raises(AttributeError):
        assignments.append(assignment)  # type: ignore[attr-defined]

    assert fabric.list_assignments() == (assignment,)


def test_fabric_assignment_record_is_immutable() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role())

    assignment = fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node_id="node-1",
        role_id="role-1",
    )

    with pytest.raises(AttributeError):
        assignment.role_id = "role-2"  # type: ignore[misc]

    assert fabric.get_assignment("assignment-1") == assignment
