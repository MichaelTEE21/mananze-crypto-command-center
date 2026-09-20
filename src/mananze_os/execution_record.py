"""Mananze OS execution record foundation contract."""

from dataclasses import dataclass

from mananze_os.authority import Authority
from mananze_os.execution_context import ExecutionContext
from mananze_os.execution_state import ExecutionState
from mananze_os.work_order import WorkOrder


@dataclass(frozen=True)
class ExecutionRecord:
    work_order: WorkOrder
    context: ExecutionContext
    authority: Authority
    state: ExecutionState


__all__ = ["ExecutionRecord"]
