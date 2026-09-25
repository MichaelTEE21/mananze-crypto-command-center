import pytest

from mananze_os.tool_catalog import TOOLS, default_tool_registry, register_default_tools
from mananze_os.tool_registry import ToolRegistry


EXPECTED_TOOL_IDS = (
    "mananze:marketing:campaign_plan",
    "mananze:marketing:content_draft",
    "mananze:sales:lead_qualification",
    "mananze:sales:follow_up_plan",
    "mananze:revenue:performance_report",
    "mananze:reporting:business_report",
    "mananze:customer_communications:message_draft",
    "mananze:logistics:route_plan",
    "mananze:fleet:fleet_status",
    "mananze:cost_analysis:cost_review",
    "mananze:operations:workflow_plan",
)


def test_default_catalog_contains_expected_tools():
    assert tuple(tool.tool_id for tool in TOOLS) == EXPECTED_TOOL_IDS


def test_default_catalog_has_unique_tool_ids():
    assert len(TOOLS) == len({tool.tool_id for tool in TOOLS})


def test_default_catalog_registers_all_tools():
    registry = default_tool_registry()

    assert tuple(tool.tool_id for tool in registry.list_all()) == EXPECTED_TOOL_IDS


def test_register_default_tools_uses_supplied_registry():
    registry = ToolRegistry()

    result = register_default_tools(registry)

    assert result is registry
    assert len(registry.list_all()) == len(EXPECTED_TOOL_IDS)


def test_tools_have_valid_governance_metadata():
    for tool in TOOLS:
        assert tool.capability_id.strip()
        assert tool.version.strip()
        assert tool.description.strip()
        assert tool.input_schema["type"] == "object"
        assert tool.output_schema["type"] == "object"
        assert tool.required_permission_ids
        assert tool.risk in {"low", "medium", "high", "critical"}
        assert tool.audit_required is True
        assert tool.execution_mode == "internal"


def test_catalog_does_not_create_execution_or_approval_authority():
    registry = default_tool_registry()

    assert not hasattr(registry, "execute")
    assert not hasattr(registry, "approve")


def test_supplied_registry_rejects_duplicate_registration():
    registry = default_tool_registry()

    with pytest.raises(ValueError, match="already registered"):
        register_default_tools(registry)
