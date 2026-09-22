import pytest

from mananze_os.action_gate import ActionGate, ActionRequest


def make_request(**overrides):
    values = {
        "action_id": "action:001",
        "tenant_id": "tenant-1",
        "execution_id": "exec:001",
        "task_id": "task:001",
        "actor_id": "actor:001",
        "tool_id": "tool:web_search",
        "capability_id": "research",
        "action": "search_web",
        "risk": "medium",
        "payload": {"query": "test"},
    }
    values.update(overrides)
    return ActionRequest(**values)


def test_action_is_allowed_when_all_gate_checks_pass():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(),
        tenant_allowed=True,
        permission_allowed=True,
        policy_effect="allow",
        economic_allowed=True,
    )

    assert decision.effect == "allow"
    assert decision.allowed is True


def test_tenant_denial_blocks_action():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(),
        tenant_allowed=False,
        permission_allowed=True,
        policy_effect="allow",
    )

    assert decision.effect == "deny"
    assert "tenant access denied" in decision.reasons


def test_permission_denial_blocks_action():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(),
        tenant_allowed=True,
        permission_allowed=False,
        policy_effect="allow",
    )

    assert decision.effect == "deny"
    assert "permission denied" in decision.reasons


def test_policy_denial_blocks_action():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(),
        tenant_allowed=True,
        permission_allowed=True,
        policy_effect="deny",
    )

    assert decision.effect == "deny"
    assert "policy denied" in decision.reasons


def test_economic_constraint_blocks_action():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(),
        tenant_allowed=True,
        permission_allowed=True,
        policy_effect="allow",
        economic_allowed=False,
    )

    assert decision.effect == "deny"
    assert "economic/resource constraint exceeded" in decision.reasons


def test_request_approval_produces_approval_required():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(requires_approval=True),
        tenant_allowed=True,
        permission_allowed=True,
        policy_effect="allow",
    )

    assert decision.effect == "approval_required"
    assert decision.allowed is False
    assert "human approval required" in decision.reasons


def test_policy_approval_produces_approval_required():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(),
        tenant_allowed=True,
        permission_allowed=True,
        policy_effect="approval_required",
    )

    assert decision.effect == "approval_required"


def test_deny_takes_precedence_over_approval():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(requires_approval=True),
        tenant_allowed=True,
        permission_allowed=False,
        policy_effect="allow",
    )

    assert decision.effect == "deny"


def test_multiple_denials_are_preserved():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(),
        tenant_allowed=False,
        permission_allowed=False,
        policy_effect="deny",
        economic_allowed=False,
    )

    assert decision.effect == "deny"
    assert len(decision.reasons) == 4


def test_invalid_action_request_is_rejected():
    with pytest.raises(ValueError, match="action_id"):
        make_request(action_id="")


def test_invalid_tenant_is_rejected():
    with pytest.raises(ValueError, match="tenant_id"):
        make_request(tenant_id="")


def test_invalid_tool_is_rejected():
    with pytest.raises(ValueError, match="tool_id"):
        make_request(tool_id="")


def test_invalid_capability_is_rejected():
    with pytest.raises(ValueError, match="capability_id"):
        make_request(capability_id="")


def test_decision_is_tenant_scoped():
    gate = ActionGate()

    decision = gate.evaluate(
        make_request(),
        tenant_allowed=True,
        permission_allowed=True,
        policy_effect="allow",
    )

    assert decision.tenant_id == "tenant-1"
    assert decision.execution_id == "exec:001"


def test_action_gate_does_not_execute_tools():
    gate = ActionGate()

    assert not hasattr(gate, "execute")
    assert not hasattr(gate, "approve")


def test_action_request_is_immutable():
    request = make_request()

    with pytest.raises(AttributeError):
        request.action_id = "action:changed"
