from mananze_os.execution_evidence import ExecutionEvidence


def test_execution_evidence_accepts_valid_record():
    evidence = ExecutionEvidence(
        execution_id="exec:1",
        action="policy_decision",
        status="approval_required",
        details="risk=medium",
    )

    assert evidence.execution_id == "exec:1"
    assert evidence.action == "policy_decision"
    assert evidence.status == "approval_required"


def test_execution_evidence_rejects_empty_execution_id():
    try:
        ExecutionEvidence(
            execution_id=" ",
            action="test",
            status="completed",
            details="",
        )
    except ValueError as exc:
        assert "execution_id is required" in str(exc)
    else:
        raise AssertionError("empty execution ID was accepted")


def test_execution_evidence_rejects_empty_action():
    try:
        ExecutionEvidence(
            execution_id="exec:1",
            action=" ",
            status="completed",
            details="",
        )
    except ValueError as exc:
        assert "action is required" in str(exc)
    else:
        raise AssertionError("empty action was accepted")


def test_execution_evidence_rejects_empty_status():
    try:
        ExecutionEvidence(
            execution_id="exec:1",
            action="test",
            status=" ",
            details="",
        )
    except ValueError as exc:
        assert "status is required" in str(exc)
    else:
        raise AssertionError("empty status was accepted")
