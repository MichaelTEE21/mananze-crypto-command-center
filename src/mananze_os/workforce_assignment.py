"""Mananze OS workforce assignment contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkforceAssignment:
    assignment_id: str
    execution_id: str
    node_id: str
    role_id: str

    def __post_init__(self) -> None:
        if not self.assignment_id.strip():
            raise ValueError("assignment_id is required")

        if not self.execution_id.strip():
            raise ValueError("execution_id is required")

        if not self.node_id.strip():
            raise ValueError("node_id is required")

        if not self.role_id.strip():
            raise ValueError("role_id is required")


__all__ = ["WorkforceAssignment"]
