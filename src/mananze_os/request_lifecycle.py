"""Mananze OS canonical request lifecycle contract."""

from dataclasses import dataclass
from typing import Literal


RequestStatus = Literal[
    "received",
    "validating",
    "classifying",
    "compiling",
    "planning",
    "scheduled",
    "waiting_approval",
    "executing",
    "verifying",
    "completed",
    "blocked",
    "failed",
    "cancelled",
    "expired",
    "retrying",
]


_ALLOWED_TRANSITIONS: dict[RequestStatus, tuple[RequestStatus, ...]] = {
    "received": ("validating", "cancelled"),
    "validating": ("classifying", "blocked", "failed", "cancelled"),
    "classifying": ("compiling", "blocked", "failed", "cancelled"),
    "compiling": ("planning", "blocked", "failed", "cancelled"),
    "planning": ("scheduled", "blocked", "failed", "cancelled"),
    "scheduled": ("waiting_approval", "executing", "blocked", "failed", "cancelled", "expired"),
    "waiting_approval": ("executing", "blocked", "cancelled", "expired"),
    "executing": ("verifying", "blocked", "failed", "cancelled"),
    "verifying": ("completed", "failed", "blocked"),
    "completed": (),
    "blocked": ("retrying", "cancelled", "expired"),
    "failed": ("retrying", "cancelled"),
    "retrying": ("scheduled", "failed", "cancelled", "expired"),
    "cancelled": (),
    "expired": (),
}


@dataclass(frozen=True)
class RequestState:
    request_id: str
    status: RequestStatus = "received"


@dataclass(frozen=True)
class RequestTransition:
    request_id: str
    from_status: RequestStatus
    to_status: RequestStatus


class RequestLifecycle:
    """Enforce the legal state transitions of a Mananze request."""

    def transition(
        self,
        state: RequestState,
        to_status: RequestStatus,
    ) -> tuple[RequestState, RequestTransition]:
        if not state.request_id.strip():
            raise ValueError("request_id is required")

        allowed = _ALLOWED_TRANSITIONS[state.status]

        if to_status not in allowed:
            raise ValueError(
                f"invalid request transition: "
                f"{state.status} -> {to_status}"
            )

        next_state = RequestState(
            request_id=state.request_id,
            status=to_status,
        )

        transition = RequestTransition(
            request_id=state.request_id,
            from_status=state.status,
            to_status=to_status,
        )

        return next_state, transition


__all__ = [
    "RequestLifecycle",
    "RequestState",
    "RequestStatus",
    "RequestTransition",
]
