"""Mananze OS workforce skill registry foundation."""

from mananze_os.skill import Skill


class SkillRegistry:
    """Registry of skills available to the Mananze workforce."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        if not skill.skill_id.strip():
            raise ValueError("skill_id is required")

        if skill.skill_id in self._skills:
            raise ValueError(
                f"skill already registered: {skill.skill_id}"
            )

        self._skills[skill.skill_id] = skill

    def get(self, skill_id: str) -> Skill:
        try:
            return self._skills[skill_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown skill: {skill_id}"
            ) from exc

    def list_all(self) -> tuple[Skill, ...]:
        return tuple(self._skills.values())


__all__ = ["SkillRegistry"]
