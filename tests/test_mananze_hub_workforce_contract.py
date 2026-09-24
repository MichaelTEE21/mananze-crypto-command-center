from mananze_hub.catalog import HubCapability
from mananze_hub.catalog_validation import validate_catalog
from mananze_os.capability_registry import default_capability_registry
from mananze_os.skill_registry import default_skill_registry
from mananze_os.tool_registry import ToolRegistry, ToolDefinition


def test_current_hub_workforce_contract_is_valid():
    errors = validate_catalog(
        os_registry=default_capability_registry(),
        skill_registry=default_skill_registry(),
    )

    assert errors == ()


def test_skill_from_wrong_os_capability_is_reported():
    capability = HubCapability(
        capability_id="mananze:test",
        name="Test",
        description="Test capability",
        os_capability_ids=("marketing",),
        required_skill_ids=("sales:follow_up",),
    )

    errors = validate_catalog(
        capabilities=(capability,),
        os_registry=default_capability_registry(),
        skill_registry=default_skill_registry(),
    )

    assert errors == (
        "mananze:test: skill sales:follow_up belongs to OS capability "
        "sales, which is not mapped",
    )


def test_tool_from_wrong_os_capability_is_reported():
    tool_registry = ToolRegistry()
    tool_registry.register(
        ToolDefinition(
            tool_id="sales:follow_up_tool",
            version="1.0.0",
            description="Sales follow-up tool.",
            capability_id="sales",
            input_schema={},
            output_schema={},
        )
    )

    capability = HubCapability(
        "mananze:test",
        "Test",
        "Test capability.",
        os_capability_ids=("marketing",),
        tool_ids=("sales:follow_up_tool",),
    )

    errors = validate_catalog(
        capabilities=(capability,),
        os_registry=default_capability_registry(),
        skill_registry=default_skill_registry(),
        tool_registry=tool_registry,
    )

    assert errors == (
        "mananze:test: tool sales:follow_up_tool belongs to OS capability "
        "sales, which is not mapped",
    )


def test_unknown_tool_is_reported():
    tool_registry = ToolRegistry()

    capability = HubCapability(
        "mananze:test",
        "Test",
        "Test capability.",
        os_capability_ids=("marketing",),
        tool_ids=("missing:tool",),
    )

    errors = validate_catalog(
        capabilities=(capability,),
        os_registry=default_capability_registry(),
        skill_registry=default_skill_registry(),
        tool_registry=tool_registry,
    )

    assert errors == (
        "mananze:test: unknown OS tool: missing:tool",
    )
