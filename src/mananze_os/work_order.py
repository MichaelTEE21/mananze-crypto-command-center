"""Mananze OS work-order foundation contract."""

from dataclasses import dataclass
from typing import Literal


WorkOrderStatus = Literal[
    "planned",
    "ready",
    "running",
    "blocked",
    "completed",
    "failed",
    "cancelled",
]


@dataclass(frozen=True)
class WorkOrder:
    work_order_id: str
    tenant_id: str
    objective: str
    status: WorkOrderStatus = "planned"
    candidate_capability_ids: tuple[str, ...] = ()


__all__ = ["WorkOrder", "WorkOrderStatus"]
