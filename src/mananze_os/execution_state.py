"""Mananze OS execution state foundation contract."""

from dataclasses import dataclass
from typing import Literal


ExecutionStatus = Literal[
    "created",
    "pending_approval",
    "approved",
    "running",
    "completed",
    "failed",
    "cancelled",
]


@dataclass(frozen=True)
class ExecutionState:
    execution_id: str
    status: ExecutionStatus = "created"


__all__ = ["ExecutionState", "ExecutionStatus"]
