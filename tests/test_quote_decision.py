from mananze_os.quote_decision import decide_quote


def test_ready_quote_proceeds_automatically():
    result = decide_quote(
        evidence_sufficient=True,
        has_conflict=False,
        requires_review=False,
    )

    assert result.decision == "automatic"
    assert result.reason == "ready"
    assert result.can_proceed_automatically is True
    assert result.must_freeze is False


def test_insufficient_evidence_freezes_quote():
    result = decide_quote(
        evidence_sufficient=False,
        has_conflict=False,
        requires_review=False,
    )

    assert result.decision == "freeze_and_notify"
    assert result.reason == "insufficient_evidence"
    assert result.must_freeze is True


def test_conflict_freezes_quote():
    result = decide_quote(
        evidence_sufficient=True,
        has_conflict=True,
        requires_review=False,
    )

    assert result.decision == "freeze_and_notify"
    assert result.reason == "conflict"


def test_review_requirement_freezes_quote():
    result = decide_quote(
        evidence_sufficient=True,
        has_conflict=False,
        requires_review=True,
    )

    assert result.decision == "freeze_and_notify"
    assert result.reason == "review_required"


def test_conflict_takes_precedence_over_review():
    result = decide_quote(
        evidence_sufficient=True,
        has_conflict=True,
        requires_review=True,
    )

    assert result.reason == "conflict"


def test_insufficient_evidence_takes_precedence_over_review():
    result = decide_quote(
        evidence_sufficient=False,
        has_conflict=False,
        requires_review=True,
    )

    assert result.reason == "insufficient_evidence"
