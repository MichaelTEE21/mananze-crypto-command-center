from mananze_os.capability_activation import (
    CapabilityActivation,
    CapabilityActivationPlan,
)
from mananze_os.capability_workforce_bridge import (
    CapabilityWorkforceBridge,
)


def _activation_plan(*capabilities):
    return CapabilityActivationPlan(
        tenant_id="tenant-001",
        twin_id="twin-001",
        activations=tuple(
            CapabilityActivation(
                capability_id=capability_id,
                status="active",
                reason="test evidence",
                supporting_truth_ids=("truth-001",),
            )
            for capability_id in capabilities
        ),
    )


def test_bridge_selects_canonical_roles_for_active_capability():
    bridge = CapabilityWorkforceBridge()

    plan = bridge.build(
        activation_plan=_activation_plan("marketing"),
        work_order_id="wo-001",
        objective="Create qualified demand",
    )

    assert plan.tenant_id == "tenant-001"
    assert plan.twin_id == "twin-001"
    assert plan.work_order_id == "wo-001"

    assert len(plan.selections) == 1

    selection = plan.selections[0]

    assert selection.capability_id == "marketing"
    assert "orchestrator:marketing" in selection.role_ids
    assert len(selection.role_ids) <= 2


def test_bridge_preserves_required_skills():
    bridge = CapabilityWorkforceBridge()

    plan = bridge.build(
        activation_plan=_activation_plan("marketing"),
        work_order_id="wo-002",
        objective="Create qualified demand",
    )

    selection = plan.selections[0]

    assert selection.skill_ids
    assert set(selection.skill_ids).issuperset(
        {
            "marketing:campaign_planning",
            "marketing:content_creation",
        }
    )


def test_bridge_creates_execution_graph_for_selected_capabilities():
    bridge = CapabilityWorkforceBridge()

    plan = bridge.build(
        activation_plan=_activation_plan("marketing", "sales"),
        work_order_id="wo-003",
        objective="Generate and convert qualified demand",
    )

    assert len(plan.execution_graph.nodes) == 2

    node_ids = {
        node.node_id
        for node in plan.execution_graph.nodes
    }

    assert "wo-003:marketing" in node_ids
    assert "wo-003:sales" in node_ids

    assert plan.execution_graph.execution_order() == (
        "wo-003:marketing",
        "wo-003:sales",
    )


def test_bridge_never_selects_the_entire_workforce():
    bridge = CapabilityWorkforceBridge()

    plan = bridge.build(
        activation_plan=_activation_plan("marketing"),
        work_order_id="wo-004",
        objective="Generate qualified demand",
    )

    selected_roles = {
        role_id
        for selection in plan.selections
        for role_id in selection.role_ids
    }

    assert len(selected_roles) < 200


def test_bridge_rejects_empty_active_capabilities():
    bridge = CapabilityWorkforceBridge()

    activation_plan = CapabilityActivationPlan(
        tenant_id="tenant-001",
        twin_id="twin-001",
        activations=(),
    )

    try:
        bridge.build(
            activation_plan=activation_plan,
            work_order_id="wo-005",
            objective="Do something",
        )
    except ValueError as exc:
        assert "active capabilities" in str(exc)
    else:
        raise AssertionError(
            "expected ValueError for empty active capabilities"
        )


def test_bridge_rejects_blank_work_order_id():
    bridge = CapabilityWorkforceBridge()

    try:
        bridge.build(
            activation_plan=_activation_plan("marketing"),
            work_order_id="",
            objective="Create qualified demand",
        )
    except ValueError as exc:
        assert "work_order_id" in str(exc)
    else:
        raise AssertionError(
            "expected ValueError for blank work_order_id"
        )
