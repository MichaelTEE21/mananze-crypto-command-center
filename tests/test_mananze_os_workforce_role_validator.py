import pytest

from mananze_os.capability_registry import default_capability_registry
from mananze_os.skill_registry import SkillRegistry
from mananze_os.skill import Skill
from mananze_os.workforce_role import WorkforceRole
from mananze_os.workforce_role_validator import WorkforceRoleValidator


def make_skill_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(
        Skill(
            skill_id="sales:lead_qualification",
            name="Lead Qualification",
            description="Qualify potential customers.",
            capability_id="sales",
        )
    )
    return registry


def make_role() -> WorkforceRole:
    return WorkforceRole(
        role_id="sales.specialist",
        name="Sales Specialist",
        description="Convert qualified opportunities into customers.",
        capability_ids=("sales",),
        skill_ids=("sales:lead_qualification",),
    )


def test_validator_accepts_valid_role() -> None:
    validator = WorkforceRoleValidator(
        default_capability_registry(),
        make_skill_registry(),
    )

    validator.validate(make_role())


def test_validator_rejects_unknown_capability() -> None:
    validator = WorkforceRoleValidator(
        default_capability_registry(),
        make_skill_registry(),
    )

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
        validator.validate(role)


def test_validator_rejects_unknown_skill() -> None:
    validator = WorkforceRoleValidator(
        default_capability_registry(),
        make_skill_registry(),
    )

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
        validator.validate(role)


def test_validator_rejects_skill_outside_role_capabilities() -> None:
    validator = WorkforceRoleValidator(
        default_capability_registry(),
        make_skill_registry(),
    )

    role = WorkforceRole(
        role_id="marketing.specialist",
        name="Marketing Specialist",
        description="Generate qualified demand.",
        capability_ids=("marketing",),
        skill_ids=("sales:lead_qualification",),
    )

    with pytest.raises(
        ValueError,
        match="skill capability is not assigned to role",
    ):
        validator.validate(role)
