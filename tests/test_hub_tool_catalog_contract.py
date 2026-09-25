from mananze_hub.catalog import CAPABILITIES
from mananze_os.tool_catalog import default_tool_registry


def test_hub_tool_ids_are_registered_in_authoritative_tool_catalog():
    registry = default_tool_registry()

    for capability in CAPABILITIES:
        for tool_id in capability.tool_ids:
            tool = registry.get(tool_id)

            assert tool.tool_id == tool_id
            assert tool.capability_id in capability.os_capability_ids


def test_hub_tool_references_are_known():
    registry = default_tool_registry()

    referenced_tool_ids = {
        tool_id
        for capability in CAPABILITIES
        for tool_id in capability.tool_ids
    }

    registered_tool_ids = {
        tool.tool_id
        for tool in registry.list_all()
    }

    assert referenced_tool_ids <= registered_tool_ids


def test_hub_tool_references_are_validated_against_their_mapped_os_capabilities():
    registry = default_tool_registry()

    for capability in CAPABILITIES:
        for tool_id in capability.tool_ids:
            tool = registry.get(tool_id)

            assert tool.capability_id in capability.os_capability_ids
