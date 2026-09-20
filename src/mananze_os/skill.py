"""Mananze OS workforce skill contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    skill_id: str
    name: str
    description: str
    capability_id: str

    def __post_init__(self) -> None:
        if not self.skill_id.strip():
            raise ValueError("skill_id is required")

        if not self.name.strip():
            raise ValueError("skill name is required")

        if not self.description.strip():
            raise ValueError("skill description is required")

        if not self.capability_id.strip():
            raise ValueError("capability_id is required")


__all__ = ["Skill"]
