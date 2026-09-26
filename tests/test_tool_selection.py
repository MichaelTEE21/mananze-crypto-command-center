from dataclasses import replace

import pytest

from mananze_os.capability_activation import (
    CapabilityActivation,
    CapabilityActivationPlan,
)
from mananze_os.capability_workforce_bridge import CapabilityWorkforceBridge
from mananze_os.tool_registry import ToolDefinition, ToolRegistry
from mananze_os.tool_selection import ToolSelectionEngine


def build_plan():
    activation = CapabilityActivationPlan(
        tenant_id="tenant-test",
        twin_id="twin:test",
        activations=(
            CapabilityActivation(
                capability_id="marketing",
                status="active",
                reason="marketing is supported",
                supporting_truth_ids=("truth:marketing",),
            ),
        ),
    )

    plan = CapabilityWorkforceBridge().build(
        activation_plan=activation,
        work_order_id="wo:tool-selection",
        objective="Create a marketing campaign",
    )

    return plan


def build_registry():
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            tool_id="mananze:marketing:campaign_plan",
            version="1.0.0",
            description="Create a governed marketing campaign plan",
            capability_id="marketing",
            input_schema={},
            output_schema={},
            supported_skill_ids=(
                "marketing:campaign_planning",
                "marketing:content_creation",
            ),
            supported_tenant_ids=("tenant-test",),
            allowed_provider_ids=("provider:test",),
            estimated_cost=1.0,
            execution_mode="external",
        )
    )

    return registry


def test_selector_binds_registered_tool_to_workforce_node():
    plan = build_plan()
    registry = build_registry()

    result = ToolSelectionEngine(registry).bind(
        plan,
        available_provider_ids=("provider:test",),
    )

    assert len(result.bindings) == 1
    assert result.bindings[0].tool_id == "mananze:marketing:campaign_plan"
    assert result.execution_graph.nodes[0].tool_id == (
        "mananze:marketing:campaign_plan"
    )


def test_selector_respects_tenant_boundary():
    plan = build_plan()
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            tool_id="mananze:marketing:wrong-tenant",
            version="1.0.0",
            description="Wrong tenant tool",
            capability_id="marketing",
            input_schema={},
            output_schema={},
            supported_skill_ids=(
                "marketing:campaign_planning",
                "marketing:content_creation",
            ),
            supported_tenant_ids=("tenant-other",),
        )
    )

    with pytest.raises(LookupError):
        ToolSelectionEngine(registry).bind(plan)


def test_selector_respects_skill_boundary():
    plan = build_plan()
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            tool_id="mananze:marketing:wrong-skills",
            version="1.0.0",
            description="Missing required workforce skills",
            capability_id="marketing",
            input_schema={},
            output_schema={},
            supported_skill_ids=("marketing:campaign_planning",),
            supported_tenant_ids=("tenant-test",),
        )
    )

    with pytest.raises(LookupError):
        ToolSelectionEngine(registry).bind(plan)


def test_selector_respects_permission_boundary():
    plan = build_plan()
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            tool_id="mananze:marketing:restricted",
            version="1.0.0",
            description="Restricted marketing tool",
            capability_id="marketing",
            input_schema={},
            output_schema={},
            supported_skill_ids=(
                "marketing:campaign_planning",
                "marketing:content_creation",
            ),
            required_permission_ids=("permission:marketing-send",),
            supported_tenant_ids=("tenant-test",),
        )
    )

    with pytest.raises(LookupError):
        ToolSelectionEngine(registry).bind(plan)


def test_selector_respects_provider_compatibility():
    plan = build_plan()
    registry = build_registry()

    with pytest.raises(LookupError):
        ToolSelectionEngine(registry).bind(
            plan,
            available_provider_ids=("provider:other",),
        )


def test_selector_rejects_prebound_nodes():
    plan = build_plan()

    node = plan.execution_graph.nodes[0]
    prebound = replace(
        plan.execution_graph,
        nodes=(
            replace(
                node,
                tool_id="mananze:already-bound",
            ),
        ),
    )

    prebound_plan = replace(
        plan,
        execution_graph=prebound,
    )

    registry = build_registry()

    with pytest.raises(ValueError):
        ToolSelectionEngine(registry).bind(prebound_plan)
