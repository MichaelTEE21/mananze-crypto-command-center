"""Mananze OS tenant boundary contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    name: str
    active: bool = True

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.name.strip():
            raise ValueError("tenant name is required")


__all__ = ["Tenant"]
