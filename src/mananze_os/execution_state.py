"""Mananze OS execution state foundation contract."""

from dataclasses import dataclass
from typing import Literal


ExecutionStatus = Literal[
    "created",
    "queued",
    "authorized",
    "pending_approval",
    "approved",
    "running",
    "waiting",
    "blocked",
    "qa",
    "executing",
    "completed",
    "failed",
    "cancelled",
    "recovering",
]


@dataclass(frozen=True)
class ExecutionState:
    execution_id: str
    status: ExecutionStatus = "created"


__all__ = ["ExecutionState", "ExecutionStatus"]
