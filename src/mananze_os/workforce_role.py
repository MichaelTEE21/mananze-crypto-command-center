"""Mananze OS workforce role contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkforceRole:
    role_id: str
    name: str
    description: str
    capability_ids: tuple[str, ...]
    skill_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.role_id.strip():
            raise ValueError("role_id is required")

        if not self.name.strip():
            raise ValueError("role name is required")

        if not self.description.strip():
            raise ValueError("role description is required")

        if not self.capability_ids:
            raise ValueError("at least one capability_id is required")

        if any(
            not capability_id.strip()
            for capability_id in self.capability_ids
        ):
            raise ValueError("capability_id is required")

        if any(
            not skill_id.strip()
            for skill_id in self.skill_ids
        ):
            raise ValueError("skill_id is required")


__all__ = ["WorkforceRole"]
