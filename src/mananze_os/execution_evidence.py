"""Mananze OS execution evidence contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionEvidence:
    execution_id: str
    action: str
    status: str
    details: str

    def __post_init__(self) -> None:
        if not self.execution_id.strip():
            raise ValueError("execution_id is required")

        if not self.action.strip():
            raise ValueError("action is required")

        if not self.status.strip():
            raise ValueError("status is required")


__all__ = ["ExecutionEvidence"]
