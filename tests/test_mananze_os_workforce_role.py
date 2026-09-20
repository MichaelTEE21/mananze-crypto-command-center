import pytest

from mananze_os.workforce_role import WorkforceRole


def test_workforce_role_can_be_created() -> None:
    role = WorkforceRole(
        role_id="sales.specialist",
        name="Sales Specialist",
        description="Convert qualified opportunities into customers.",
        capability_ids=("sales",),
        skill_ids=("sales:lead_qualification",),
    )

    assert role.role_id == "sales.specialist"
    assert role.capability_ids == ("sales",)
    assert role.skill_ids == ("sales:lead_qualification",)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("role_id", "", "role_id is required"),
        ("name", "", "role name is required"),
        ("description", "", "role description is required"),
    ),
)
def test_workforce_role_rejects_missing_text_fields(
    field: str,
    value: str,
    message: str,
) -> None:
    values = {
        "role_id": "sales.specialist",
        "name": "Sales Specialist",
        "description": "Convert qualified opportunities into customers.",
        "capability_ids": ("sales",),
        "skill_ids": ("sales:lead_qualification",),
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        WorkforceRole(**values)


def test_workforce_role_requires_capability() -> None:
    with pytest.raises(
        ValueError,
        match="at least one capability_id is required",
    ):
        WorkforceRole(
            role_id="sales.specialist",
            name="Sales Specialist",
            description="Convert qualified opportunities into customers.",
            capability_ids=(),
            skill_ids=("sales:lead_qualification",),
        )


def test_workforce_role_rejects_blank_capability_id() -> None:
    with pytest.raises(ValueError, match="capability_id is required"):
        WorkforceRole(
            role_id="sales.specialist",
            name="Sales Specialist",
            description="Convert qualified opportunities into customers.",
            capability_ids=(" ",),
            skill_ids=("sales:lead_qualification",),
        )


def test_workforce_role_rejects_blank_skill_id() -> None:
    with pytest.raises(ValueError, match="skill_id is required"):
        WorkforceRole(
            role_id="sales.specialist",
            name="Sales Specialist",
            description="Convert qualified opportunities into customers.",
            capability_ids=("sales",),
            skill_ids=(" ",),
        )
