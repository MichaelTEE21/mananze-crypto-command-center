"""Mananze OS capability permission contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityPermission:
    actor_id: str
    tenant_id: str
    capability_id: str
    allowed: bool = True

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("actor_id is required")

        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.capability_id.strip():
            raise ValueError("capability_id is required")


__all__ = ["CapabilityPermission"]
