"""Mananze OS execution lifecycle controller."""

from dataclasses import dataclass

from mananze_os.execution_state import ExecutionState, ExecutionStatus


_ALLOWED_TRANSITIONS: dict[ExecutionStatus, tuple[ExecutionStatus, ...]] = {
    "created": ("pending_approval", "cancelled"),
    "pending_approval": ("approved", "cancelled"),
    "approved": ("running", "cancelled"),
    "running": ("completed", "failed", "cancelled"),
    "completed": (),
    "failed": (),
    "cancelled": (),
}


@dataclass(frozen=True)
class ExecutionTransition:
    execution_id: str
    from_status: ExecutionStatus
    to_status: ExecutionStatus


class ExecutionLifecycle:
    """Enforce the legal state transitions of a Mananze execution."""

    def transition(
        self,
        state: ExecutionState,
        to_status: ExecutionStatus,
    ) -> tuple[ExecutionState, ExecutionTransition]:
        if not state.execution_id.strip():
            raise ValueError("execution_id is required")

        allowed = _ALLOWED_TRANSITIONS[state.status]

        if to_status not in allowed:
            raise ValueError(
                f"invalid execution transition: "
                f"{state.status} -> {to_status}"
            )

        next_state = ExecutionState(
            execution_id=state.execution_id,
            status=to_status,
        )

        transition = ExecutionTransition(
            execution_id=state.execution_id,
            from_status=state.status,
            to_status=to_status,
        )

        return next_state, transition


__all__ = [
    "ExecutionLifecycle",
    "ExecutionTransition",
]
