from dataclasses import FrozenInstanceError

import pytest

from mananze_os.tool_registry import ToolDefinition


def test_tool_definition_accepts_supported_skill_ids():
    tool = ToolDefinition(
        tool_id="test:tool",
        version="1.0.0",
        description="Test tool",
        capability_id="test_capability",
        input_schema={},
        output_schema={},
        supported_skill_ids=("test:skill",),
    )

    assert tool.supported_skill_ids == ("test:skill",)


def test_tool_definition_rejects_blank_supported_skill_id():
    with pytest.raises(ValueError, match="supported skill IDs"):
        ToolDefinition(
            tool_id="test:tool",
            version="1.0.0",
            description="Test tool",
            capability_id="test_capability",
            input_schema={},
            output_schema={},
            supported_skill_ids=(" ",),
        )


def test_tool_definition_remains_frozen():
    tool = ToolDefinition(
        tool_id="test:tool",
        version="1.0.0",
        description="Test tool",
        capability_id="test_capability",
        input_schema={},
        output_schema={},
        supported_skill_ids=("test:skill",),
    )

    with pytest.raises(FrozenInstanceError):
        tool.supported_skill_ids = ("other:skill",)
