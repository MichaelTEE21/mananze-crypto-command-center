from mananze_os.execution_lifecycle import ExecutionLifecycle
from mananze_os.execution_state import ExecutionState


def test_execution_lifecycle_allows_controlled_progression():
    lifecycle = ExecutionLifecycle()
    state = ExecutionState("exec:1")

    state, transition = lifecycle.transition(
        state,
        "pending_approval",
    )
    assert state.status == "pending_approval"
    assert transition.from_status == "created"

    state, transition = lifecycle.transition(
        state,
        "approved",
    )
    assert state.status == "approved"
    assert transition.to_status == "approved"

    state, transition = lifecycle.transition(
        state,
        "running",
    )
    assert state.status == "running"

    state, transition = lifecycle.transition(
        state,
        "completed",
    )
    assert state.status == "completed"


def test_execution_lifecycle_allows_failure_from_running():
    lifecycle = ExecutionLifecycle()
    state = ExecutionState("exec:2", "running")

    state, transition = lifecycle.transition(
        state,
        "failed",
    )

    assert state.status == "failed"
    assert transition.from_status == "running"
    assert transition.to_status == "failed"


def test_execution_lifecycle_allows_cancellation_before_execution():
    lifecycle = ExecutionLifecycle()
    state = ExecutionState("exec:3", "pending_approval")

    state, transition = lifecycle.transition(
        state,
        "cancelled",
    )

    assert state.status == "cancelled"
    assert transition.to_status == "cancelled"


def test_execution_lifecycle_rejects_invalid_transition():
    lifecycle = ExecutionLifecycle()
    state = ExecutionState("exec:4", "created")

    try:
        lifecycle.transition(state, "completed")
    except ValueError as exc:
        assert "invalid execution transition" in str(exc)
    else:
        raise AssertionError("invalid transition was accepted")


def test_execution_lifecycle_rejects_transition_from_terminal_state():
    lifecycle = ExecutionLifecycle()
    state = ExecutionState("exec:5", "completed")

    try:
        lifecycle.transition(state, "running")
    except ValueError as exc:
        assert "invalid execution transition" in str(exc)
    else:
        raise AssertionError("terminal transition was accepted")


def test_execution_lifecycle_rejects_empty_execution_id():
    lifecycle = ExecutionLifecycle()
    state = ExecutionState(" ")

    try:
        lifecycle.transition(state, "pending_approval")
    except ValueError as exc:
        assert "execution_id is required" in str(exc)
    else:
        raise AssertionError("empty execution ID was accepted")
