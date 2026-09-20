"""Mananze OS approval foundation contract."""

from dataclasses import dataclass
from typing import Literal


ApprovalStatus = Literal[
    "not_required",
    "pending",
    "approved",
    "rejected",
]


@dataclass(frozen=True)
class ApprovalDecision:
    approval_id: str
    execution_id: str
    status: ApprovalStatus
    decided_by: str | None = None
    reason: str | None = None


__all__ = ["ApprovalDecision", "ApprovalStatus"]
