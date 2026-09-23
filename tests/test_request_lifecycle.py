import pytest

from mananze_os.request_lifecycle import (
    RequestLifecycle,
    RequestState,
)


def test_request_lifecycle_supports_canonical_happy_path():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-001")

    expected = [
        "validating",
        "classifying",
        "compiling",
        "planning",
        "scheduled",
        "waiting_approval",
        "executing",
        "verifying",
        "completed",
    ]

    for status in expected:
        state, transition = lifecycle.transition(state, status)
        assert transition.request_id == "req-001"
        assert transition.to_status == status
        assert state.status == status


def test_request_lifecycle_rejects_invalid_transition():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-002")

    with pytest.raises(ValueError, match="invalid request transition"):
        lifecycle.transition(state, "completed")


def test_request_lifecycle_requires_request_id():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="")

    with pytest.raises(ValueError, match="request_id is required"):
        lifecycle.transition(state, "validating")


def test_completed_request_is_terminal():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-003", status="completed")

    with pytest.raises(ValueError, match="invalid request transition"):
        lifecycle.transition(state, "executing")


def test_failed_request_can_retry():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-004", status="failed")

    state, transition = lifecycle.transition(state, "retrying")

    assert transition.from_status == "failed"
    assert transition.to_status == "retrying"
    assert state.status == "retrying"


def test_retrying_request_returns_to_scheduled():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-005", status="retrying")

    state, _ = lifecycle.transition(state, "scheduled")

    assert state.status == "scheduled"


def test_cancelled_request_is_terminal():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-006", status="cancelled")

    with pytest.raises(ValueError, match="invalid request transition"):
        lifecycle.transition(state, "retrying")


def test_expired_request_is_terminal():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-007", status="expired")

    with pytest.raises(ValueError, match="invalid request transition"):
        lifecycle.transition(state, "scheduled")


def test_blocked_request_can_recover():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-008", status="blocked")

    state, _ = lifecycle.transition(state, "retrying")

    assert state.status == "retrying"


def test_request_lifecycle_does_not_skip_approval_boundary():
    lifecycle = RequestLifecycle()
    state = RequestState(request_id="req-009", status="scheduled")

    with pytest.raises(ValueError, match="invalid request transition"):
        lifecycle.transition(state, "verifying")
