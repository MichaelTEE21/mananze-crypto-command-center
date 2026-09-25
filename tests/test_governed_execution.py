import pytest

from mananze_os.action_gate import ActionGate
from mananze_os.authority import Authority
from mananze_os.capability_activation import (
    CapabilityActivation,
    CapabilityActivationPlan,
)
from mananze_os.capability_workforce_bridge import (
    CapabilityWorkforceBridge,
)
from mananze_os.governed_execution import (
    GovernedExecutionController,
)
from mananze_os.permission import CapabilityPermission
from mananze_os.policy import Policy
from mananze_os.tenant import Tenant


def _plan(*capabilities):
    activation = CapabilityActivationPlan(
        tenant_id="tenant-demo",
        twin_id="twin-demo",
        activations=tuple(
            CapabilityActivation(
                capability_id=capability,
                status="active",
                reason="test evidence",
                supporting_truth_ids=("truth-001",),
            )
            for capability in capabilities
        ),
    )

    return CapabilityWorkforceBridge().build(
        activation_plan=activation,
        work_order_id="wo-governed-001",
        objective="Create qualified demand",
    )


def _authority(
    *,
    actor_id="human:tshepo",
    can_execute=True,
):
    return Authority(
        actor_id=actor_id,
        level="human",
        can_execute=can_execute,
        requires_approval=True,
    )


def _permissions(*capabilities):
    return tuple(
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id=capability,
        )
        for capability in capabilities
    )


def _evaluate(
    *,
    plan=None,
    authority=None,
    tenant=None,
    permissions=None,
    capability_id="marketing",
    action="prepare_campaign",
    **overrides,
):
    return GovernedExecutionController().evaluate(
        plan=plan or _plan("marketing"),
        execution_id="exec:wo-governed-001",
        task_id="task:wo-governed-001",
        actor_id="human:tshepo",
        capability_id=capability_id,
        action=action,
        authority=authority or _authority(),
        tenant=tenant or Tenant(
            tenant_id="tenant-demo",
            name="Demo Tenant",
        ),
        permissions=(
            permissions
            if permissions is not None
            else _permissions("marketing")
        ),
        **overrides,
    )


def test_valid_action_reaches_allowed_boundary():
    result = _evaluate()

    assert result.disposition == "allowed"
    assert result.allowed is True
    assert result.requires_approval is False

    assert result.context is not None
    assert result.context.execution_id == "exec:wo-governed-001"
    assert result.context.task_id == "task:wo-governed-001"

    assert result.authorization is not None
    assert result.authorization.allowed is True

    assert result.action_request is not None
    assert result.action_request.tenant_id == "tenant-demo"
    assert result.action_request.capability_id == "marketing"


def test_missing_permission_stops_execution():
    result = _evaluate(permissions=())

    assert result.disposition == "denied"
    assert result.allowed is False
    assert result.authorization is not None
    assert result.authorization.allowed is False
    assert any(
        "missing permission" in reason
        for reason in result.reasons
    )


def test_inactive_tenant_stops_execution():
    tenant = Tenant(
        tenant_id="tenant-demo",
        name="Demo Tenant",
        active=False,
    )

    result = _evaluate(tenant=tenant)

    assert result.disposition == "denied"
    assert result.authorization is not None
    assert result.authorization.allowed is False
    assert "tenant is inactive" in result.reasons


def test_authority_without_execution_permission_stops_execution():
    result = _evaluate(
        authority=_authority(can_execute=False),
    )

    assert result.disposition == "denied"
    assert result.authorization is not None
    assert result.authorization.allowed is False
    assert "authority does not permit execution" in result.reasons


def test_policy_denial_stops_execution():
    policy = Policy(
        policy_id="policy-deny-marketing",
        name="Deny marketing",
        effect="deny",
        description="Marketing denied for this test.",
        capability_ids=("marketing",),
    )

    result = _evaluate(
        policy=(policy,),
    )

    assert result.disposition == "denied"
    assert result.policy is not None
    assert result.policy.effect == "deny"
    assert result.authorization is None


def test_action_gate_denial_stops_execution():
    result = _evaluate(
        economic_allowed=False,
    )

    assert result.disposition == "denied"
    assert result.action_request is not None
    assert any(
        "economic/resource constraint exceeded" in reason
        for reason in result.reasons
    )


def test_action_gate_approval_creates_pending_approval():
    result = _evaluate(
        requires_approval=True,
    )

    assert result.disposition == "approval_required"
    assert result.allowed is False
    assert result.requires_approval is True

    assert result.approval is not None
    assert result.approval.status == "pending"
    assert result.approval.decided_by is None

    assert result.action_request is not None
    assert result.action_request.requires_approval is True


def test_approval_is_never_granted_by_controller():
    result = _evaluate(
        requires_approval=True,
    )

    assert result.approval is not None
    assert result.approval.status == "pending"
    assert result.approval.decided_by is None


def test_execution_lineage_is_preserved():
    result = _evaluate()

    assert result.execution_id == "exec:wo-governed-001"
    assert result.task_id == "task:wo-governed-001"
    assert result.work_order_id == "wo-governed-001"
    assert result.tenant_id == "tenant-demo"
    assert result.actor_id == "human:tshepo"
    assert result.capability_id == "marketing"

    assert result.action_request is not None
    assert result.action_request.execution_id == result.execution_id
    assert result.action_request.task_id == result.task_id
    assert result.action_request.tenant_id == result.tenant_id
    assert result.action_request.actor_id == result.actor_id
    assert result.action_request.capability_id == result.capability_id


@pytest.mark.parametrize(
    ("execution_id", "task_id", "match"),
    (
        ("exec:wrong", "task:wo-governed-001", "execution_id"),
        ("exec:wo-governed-001", "task:wrong", "task_id"),
    ),
)
def test_invalid_execution_lineage_is_rejected(
    execution_id,
    task_id,
    match,
):
    controller = GovernedExecutionController()

    with pytest.raises(ValueError, match=match):
        controller.evaluate(
            plan=_plan("marketing"),
            execution_id=execution_id,
            task_id=task_id,
            actor_id="human:tshepo",
            capability_id="marketing",
            action="prepare_campaign",
            authority=_authority(),
            tenant=Tenant(
                tenant_id="tenant-demo",
                name="Demo Tenant",
            ),
            permissions=_permissions("marketing"),
        )



def test_controller_does_not_execute_external_tools():
    controller = GovernedExecutionController()

    assert not hasattr(controller, "execute")
    assert not hasattr(controller, "approve")


def test_intelligence_is_not_an_input_to_authorization():
    result = _evaluate(
        permissions=(),
    )

    assert result.authorization is not None
    assert result.authorization.allowed is False
    assert result.approval is None
def test_wrong_tool_is_rejected():
    from dataclasses import replace

    controller = GovernedExecutionController()
    original_plan = _plan("marketing")

    original_node = original_plan.execution_graph.nodes[0]
    tool_bound_node = replace(original_node, tool_id="expected-tool")

    tool_bound_graph = replace(
        original_plan.execution_graph,
        nodes=(tool_bound_node,),
    )

    plan = replace(
        original_plan,
        execution_graph=tool_bound_graph,
    )

    with pytest.raises(
        ValueError,
        match="tool_id does not match",
    ):
        controller.evaluate(
            plan=plan,
            execution_id="exec:wo-governed-001",
            task_id="task:wo-governed-001",
            actor_id="human:tshepo",
            capability_id="marketing",
            action="prepare_campaign",
            authority=_authority(),
            tenant=Tenant(
                tenant_id="tenant-demo",
                name="Demo Tenant",
            ),
            permissions=_permissions("marketing"),
            tool_id="wrong-tool",
        )
