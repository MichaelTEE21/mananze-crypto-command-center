"""Mananze OS execution lifecycle controller."""

from dataclasses import dataclass

from mananze_os.execution_state import ExecutionState, ExecutionStatus


_ALLOWED_TRANSITIONS: dict[ExecutionStatus, tuple[ExecutionStatus, ...]] = {
    "created": ("queued", "pending_approval", "cancelled"),
    "queued": ("authorized", "cancelled"),
    "authorized": ("pending_approval", "running", "cancelled"),
    "pending_approval": ("approved", "cancelled"),
    "approved": ("running", "cancelled"),
    "running": ("waiting", "blocked", "qa", "executing", "completed", "failed", "cancelled"),
    "waiting": ("running", "blocked", "cancelled"),
    "blocked": ("waiting", "running", "recovering", "cancelled"),
    "qa": ("executing", "failed", "blocked", "cancelled"),
    "executing": ("completed", "failed", "cancelled", "recovering"),
    "recovering": ("queued", "failed", "cancelled"),
    "completed": (),
    "failed": ("recovering",),
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
