from mananze_os.execution_evidence import ExecutionEvidence
from mananze_os.execution_state import ExecutionState
from mananze_os.execution_verifier import ExecutionVerifier


def _complete_evidence(execution_id: str) -> tuple[ExecutionEvidence, ...]:
    return (
        ExecutionEvidence(
            execution_id=execution_id,
            action="policy_decision",
            status="approval_required",
            details="policy verified",
        ),
        ExecutionEvidence(
            execution_id=execution_id,
            action="authorization_decision",
            status="allowed",
            details="authorization verified",
        ),
        ExecutionEvidence(
            execution_id=execution_id,
            action="workforce_assignment",
            status="validated",
            details="workforce assignment verified",
        ),
        ExecutionEvidence(
            execution_id=execution_id,
            action="controlled_execution",
            status="completed",
            details="execution completed",
        ),
    )


def test_execution_verifier_accepts_complete_execution():
    verifier = ExecutionVerifier()
    result = verifier.verify(
        ExecutionState("exec:1", "completed"),
        _complete_evidence("exec:1"),
    )

    assert result.verified is True
    assert result.execution_id == "exec:1"


def test_execution_verifier_rejects_missing_required_evidence():
    verifier = ExecutionVerifier()
    evidence = _complete_evidence("exec:2")[:2]

    result = verifier.verify(
        ExecutionState("exec:2", "completed"),
        evidence,
    )

    assert result.verified is False
    assert "controlled_execution" in result.reasons[0]


def test_execution_verifier_rejects_cross_execution_evidence():
    verifier = ExecutionVerifier()

    result = verifier.verify(
        ExecutionState("exec:3", "completed"),
        _complete_evidence("exec:other"),
    )

    assert result.verified is False
    assert "execution ID mismatch" in result.reasons[0]


def test_execution_verifier_accepts_failed_execution_without_completion_evidence():
    verifier = ExecutionVerifier()

    result = verifier.verify(
        ExecutionState("exec:4", "failed"),
        (),
    )

    assert result.verified is True


def test_execution_verifier_rejects_empty_execution_id():
    verifier = ExecutionVerifier()

    try:
        verifier.verify(
            ExecutionState(" "),
            (),
        )
    except ValueError as exc:
        assert "execution_id is required" in str(exc)
    else:
        raise AssertionError("empty execution ID was accepted")
