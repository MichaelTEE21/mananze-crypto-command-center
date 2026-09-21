import pytest

from mananze_os.skill import Skill
from mananze_os.skill_registry import SkillRegistry


def make_skill(skill_id: str = "sales:lead_qualification") -> Skill:
    return Skill(
        skill_id=skill_id,
        name="Lead Qualification",
        description="Qualify potential customers.",
        capability_id="sales",
    )


def test_registry_registers_and_retrieves_skill() -> None:
    registry = SkillRegistry()
    skill = make_skill()

    registry.register(skill)

    assert registry.get("sales:lead_qualification") == skill


def test_registry_lists_skills() -> None:
    registry = SkillRegistry()
    skill_one = make_skill("sales:lead_qualification")
    skill_two = make_skill("sales:closing")

    registry.register(skill_one)
    registry.register(skill_two)

    assert registry.list_all() == (skill_one, skill_two)


def test_registry_rejects_duplicate_skill() -> None:
    registry = SkillRegistry()
    registry.register(make_skill())

    with pytest.raises(
        ValueError,
        match="skill already registered: sales:lead_qualification",
    ):
        registry.register(make_skill())


def test_registry_rejects_unknown_skill() -> None:
    registry = SkillRegistry()

    with pytest.raises(
        KeyError,
        match="unknown skill: missing-skill",
    ):
        registry.get("missing-skill")
