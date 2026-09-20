import pytest

from mananze_os.skill import Skill


def test_skill_can_be_created() -> None:
    skill = Skill(
        skill_id="sales:lead_qualification",
        name="Lead Qualification",
        description="Qualify potential customers.",
        capability_id="sales",
    )

    assert skill.skill_id == "sales:lead_qualification"
    assert skill.capability_id == "sales"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("skill_id", "", "skill_id is required"),
        ("name", "", "skill name is required"),
        ("description", "", "skill description is required"),
        ("capability_id", "", "capability_id is required"),
    ),
)
def test_skill_rejects_missing_required_fields(
    field: str,
    value: str,
    message: str,
) -> None:
    values = {
        "skill_id": "sales:lead_qualification",
        "name": "Lead Qualification",
        "description": "Qualify potential customers.",
        "capability_id": "sales",
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        Skill(**values)
