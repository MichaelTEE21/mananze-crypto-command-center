"""Mananze OS workforce role validation."""

from mananze_os.capability_registry import CapabilityRegistry
from mananze_os.skill_registry import SkillRegistry
from mananze_os.workforce_role import WorkforceRole


class WorkforceRoleValidator:
    """Validate workforce role references against registered capabilities and skills."""

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        skill_registry: SkillRegistry,
    ) -> None:
        self.capability_registry = capability_registry
        self.skill_registry = skill_registry

    def validate(self, role: WorkforceRole) -> None:
        for capability_id in role.capability_ids:
            try:
                self.capability_registry.get(capability_id)
            except KeyError as exc:
                raise ValueError(
                    f"unknown capability: {capability_id}"
                ) from exc

        for skill_id in role.skill_ids:
            try:
                skill = self.skill_registry.get(skill_id)
            except KeyError as exc:
                raise ValueError(
                    f"unknown skill: {skill_id}"
                ) from exc

            if skill.capability_id not in role.capability_ids:
                raise ValueError(
                    "skill capability is not assigned to role"
                )


__all__ = ["WorkforceRoleValidator"]
