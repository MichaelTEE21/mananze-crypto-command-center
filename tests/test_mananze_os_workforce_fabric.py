import pytest

from mananze_os.execution_graph import ExecutionNode
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


def make_node(node_id: str = "node-1") -> ExecutionNode:
    return ExecutionNode(
        node_id=node_id,
        capability_id="execution",
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
        node=make_node(),
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
            node=make_node(),
            role_id="missing-role",
        )


def test_fabric_retrieves_assignment() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role())

    assignment = fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node=make_node(),
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
        node=make_node("node-1"),
        role_id="role-1",
    )
    assignment_two = fabric.assign_role(
        assignment_id="assignment-2",
        execution_id="execution-1",
        node=make_node("node-2"),
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
        node=make_node("node-1"),
        role_id="role-1",
    )

    with pytest.raises(
        ValueError,
        match="assignment already exists: assignment-1",
    ):
        fabric.assign_role(
            assignment_id="assignment-1",
            execution_id="execution-2",
            node=make_node("node-2"),
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
        node=make_node(),
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
        node=make_node(),
        role_id="role-1",
    )

    with pytest.raises(AttributeError):
        assignment.role_id = "role-2"  # type: ignore[misc]

    assert fabric.get_assignment("assignment-1") == assignment


def test_fabric_lists_assignments_for_execution() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role("role-1"))
    fabric.register_role(make_role("role-2"))

    assignment_one = fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node=make_node("node-1"),
        role_id="role-1",
    )
    assignment_two = fabric.assign_role(
        assignment_id="assignment-2",
        execution_id="execution-1",
        node=make_node("node-2"),
        role_id="role-2",
    )
    assignment_three = fabric.assign_role(
        assignment_id="assignment-3",
        execution_id="execution-2",
        node=make_node("node-3"),
        role_id="role-1",
    )

    assert fabric.list_assignments_for_execution("execution-1") == (
        assignment_one,
        assignment_two,
    )
    assert fabric.list_assignments_for_execution("execution-2") == (
        assignment_three,
    )


def test_fabric_returns_empty_assignments_for_unknown_execution() -> None:
    fabric = WorkforceFabric()

    assert fabric.list_assignments_for_execution(
        "missing-execution"
    ) == ()


def test_fabric_rejects_blank_execution_lookup() -> None:
    fabric = WorkforceFabric()

    with pytest.raises(
        ValueError,
        match="execution_id is required",
    ):
        fabric.list_assignments_for_execution("")


from mananze_os.capability_registry import Capability, CapabilityRegistry
from mananze_os.skill import Skill
from mananze_os.skill_registry import SkillRegistry


def make_validated_fabric() -> WorkforceFabric:
    capability_registry = CapabilityRegistry()
    capability_registry.register(
        Capability(
            capability_id="sales",
            name="Sales",
            description="Convert opportunities into customers.",
            domains=("business", "sales"),
        )
    )

    skill_registry = SkillRegistry()
    skill_registry.register(
        Skill(
            skill_id="sales:lead_qualification",
            name="Lead Qualification",
            description="Qualify potential customers.",
            capability_id="sales",
        )
    )

    return WorkforceFabric(
        capability_registry=capability_registry,
        skill_registry=skill_registry,
    )


def test_fabric_validates_role_against_registries() -> None:
    fabric = make_validated_fabric()

    role = WorkforceRole(
        role_id="sales.specialist",
        name="Sales Specialist",
        description="Convert qualified opportunities into customers.",
        capability_ids=("sales",),
        skill_ids=("sales:lead_qualification",),
    )

    fabric.register_role(role)

    assert fabric.get_role("sales.specialist") == role


def test_fabric_rejects_role_with_unknown_capability() -> None:
    fabric = make_validated_fabric()

    role = WorkforceRole(
        role_id="sales.specialist",
        name="Sales Specialist",
        description="Convert qualified opportunities into customers.",
        capability_ids=("missing-capability",),
        skill_ids=(),
    )

    with pytest.raises(
        ValueError,
        match="unknown capability: missing-capability",
    ):
        fabric.register_role(role)


def test_fabric_rejects_role_with_unknown_skill() -> None:
    fabric = make_validated_fabric()

    role = WorkforceRole(
        role_id="sales.specialist",
        name="Sales Specialist",
        description="Convert qualified opportunities into customers.",
        capability_ids=("sales",),
        skill_ids=("missing-skill",),
    )

    with pytest.raises(
        ValueError,
        match="unknown skill: missing-skill",
    ):
        fabric.register_role(role)


def test_fabric_rejects_duplicate_node_assignment_within_execution() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role("role-1"))
    fabric.register_role(make_role("role-2"))

    fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node=make_node("node-1"),
        role_id="role-1",
    )

    with pytest.raises(
        ValueError,
        match="workforce node already assigned for execution: execution-1:node-1",
    ):
        fabric.assign_role(
            assignment_id="assignment-2",
            execution_id="execution-1",
            node=make_node("node-1"),
            role_id="role-2",
        )


def test_fabric_allows_same_node_id_across_executions() -> None:
    fabric = WorkforceFabric()
    fabric.register_role(make_role())

    assignment_one = fabric.assign_role(
        assignment_id="assignment-1",
        execution_id="execution-1",
        node=make_node("node-1"),
        role_id="role-1",
    )

    assignment_two = fabric.assign_role(
        assignment_id="assignment-2",
        execution_id="execution-2",
        node=make_node("node-1"),
        role_id="role-1",
    )

    assert assignment_one.node_id == assignment_two.node_id
    assert assignment_one.execution_id != assignment_two.execution_id
