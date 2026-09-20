import pytest

from mananze_os.workforce_assignment import WorkforceAssignment


def test_workforce_assignment_can_be_created() -> None:
    assignment = WorkforceAssignment(
        assignment_id="assignment:001",
        execution_id="execution:001",
        node_id="sales",
        role_id="sales.specialist",
    )

    assert assignment.assignment_id == "assignment:001"
    assert assignment.execution_id == "execution:001"
    assert assignment.node_id == "sales"
    assert assignment.role_id == "sales.specialist"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("assignment_id", "", "assignment_id is required"),
        ("execution_id", "", "execution_id is required"),
        ("node_id", "", "node_id is required"),
        ("role_id", "", "role_id is required"),
    ),
)
def test_workforce_assignment_rejects_missing_fields(
    field: str,
    value: str,
    message: str,
) -> None:
    values = {
        "assignment_id": "assignment:001",
        "execution_id": "execution:001",
        "node_id": "sales",
        "role_id": "sales.specialist",
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        WorkforceAssignment(**values)
