import pytest

from mananze_os.processing_mode_decision import (
    ProcessingModeDecider,
    ProcessingModeDecision,
)


def test_decider_preserves_explicit_processing_mode():
    decision = ProcessingModeDecider().decide("async")

    assert decision.processing_mode == "async"
    assert decision.request_blocking is False
    assert decision.reason == "explicit_request_mode"


@pytest.mark.parametrize(
    ("mode", "request_blocking"),
    (
        ("standard", True),
        ("sync", True),
        ("fast", True),
        ("async", False),
        ("background", False),
        ("event", False),
        ("batch", False),
    ),
)
def test_decider_classifies_existing_modes(mode, request_blocking):
    decision = ProcessingModeDecider().decide(mode)

    assert decision.processing_mode == mode
    assert decision.request_blocking is request_blocking


def test_decision_rejects_inconsistent_blocking_classification():
    with pytest.raises(
        ValueError,
        match="request_blocking does not match processing_mode",
    ):
        ProcessingModeDecision(
            processing_mode="async",
            request_blocking=True,
        )


def test_decider_rejects_unsupported_mode():
    with pytest.raises(
        ValueError,
        match="unsupported processing mode",
    ):
        ProcessingModeDecider().decide("unknown")


def test_decider_rejects_empty_mode():
    with pytest.raises(
        ValueError,
        match="processing_mode is required",
    ):
        ProcessingModeDecider().decide("")
