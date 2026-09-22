"""Mananze OS execution context and lineage contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionContext:
    """Tenant-scoped context carried through an execution lineage."""

    execution_id: str
    tenant_id: str
    work_order_id: str
    actor_id: str
    task_id: str = ""
    agent_id: str = ""
    parent_execution_id: str | None = None
    correlation_id: str = ""

    def __post_init__(self) -> None:
        required_fields = {
            "execution_id": self.execution_id,
            "tenant_id": self.tenant_id,
            "work_order_id": self.work_order_id,
            "actor_id": self.actor_id,
        }

        for field_name, value in required_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")

        optional_string_fields = {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "correlation_id": self.correlation_id,
        }

        for field_name, value in optional_string_fields.items():
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")

        if self.parent_execution_id is not None:
            if not isinstance(self.parent_execution_id, str):
                raise TypeError("parent_execution_id must be a string or None")

            if not self.parent_execution_id.strip():
                raise ValueError("parent_execution_id cannot be blank")


__all__ = ["ExecutionContext"]
