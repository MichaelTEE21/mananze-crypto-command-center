"""Mananze OS execution context foundation contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionContext:
    execution_id: str
    tenant_id: str
    work_order_id: str
    actor_id: str


__all__ = ["ExecutionContext"]
