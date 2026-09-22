import pytest

from mananze_os.tool_registry import ToolDefinition, ToolRegistry


def make_tool(**overrides):
    values = {
        "tool_id": "tool:web_search",
        "version": "1.0.0",
        "description": "Searches approved external web sources.",
        "capability_id": "research",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "required_permission_ids": ("permission:web_search",),
        "risk": "medium",
        "supported_tenant_ids": ("tenant-1",),
        "estimated_cost": 0.50,
        "cost_currency": "ZAR",
        "timeout_seconds": 20.0,
        "max_attempts": 2,
        "execution_mode": "external",
        "audit_required": True,
        "requires_approval": False,
    }
    values.update(overrides)
    return ToolDefinition(**values)


def test_register_and_get_tool():
    registry = ToolRegistry()
    tool = make_tool()

    registry.register(tool)

    assert registry.get("tool:web_search") == tool


def test_duplicate_tool_is_rejected():
    registry = ToolRegistry()
    tool = make_tool()

    registry.register(tool)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(tool)


def test_unknown_tool_is_rejected():
    registry = ToolRegistry()

    with pytest.raises(KeyError, match="unknown tool"):
        registry.get("tool:missing")


def test_tools_can_be_selected_by_capability():
    registry = ToolRegistry()
    first = make_tool(tool_id="tool:first")
    second = make_tool(tool_id="tool:second")
    unrelated = make_tool(
        tool_id="tool:other",
        capability_id="reporting",
    )

    registry.register(first)
    registry.register(second)
    registry.register(unrelated)

    result = registry.tools_for_capability("research")

    assert result == (first, second)


def test_supported_tenant_is_checked():
    registry = ToolRegistry()
    registry.register(make_tool())

    assert registry.supports_tenant("tool:web_search", "tenant-1") is True
    assert registry.supports_tenant("tool:web_search", "tenant-2") is False


def test_empty_tenant_restriction_means_registry_level_unrestricted():
    registry = ToolRegistry()
    registry.register(make_tool(supported_tenant_ids=()))

    assert registry.supports_tenant("tool:web_search", "tenant-1") is True
    assert registry.supports_tenant("tool:web_search", "tenant-2") is True


def test_invalid_cost_is_rejected():
    with pytest.raises(ValueError, match="estimated_cost"):
        make_tool(estimated_cost=-1)


def test_invalid_timeout_is_rejected():
    with pytest.raises(ValueError, match="timeout"):
        make_tool(timeout_seconds=0)


def test_invalid_attempt_count_is_rejected():
    with pytest.raises(ValueError, match="attempts"):
        make_tool(max_attempts=0)


def test_permission_requirements_are_preserved():
    tool = make_tool(
        required_permission_ids=(
            "permission:web_search",
            "permission:external_access",
        )
    )

    assert tool.required_permission_ids == (
        "permission:web_search",
        "permission:external_access",
    )


def test_risk_and_approval_requirements_are_preserved():
    tool = make_tool(
        risk="high",
        requires_approval=True,
    )

    assert tool.risk == "high"
    assert tool.requires_approval is True


def test_registry_does_not_grant_execution_permission():
    registry = ToolRegistry()
    tool = make_tool(requires_approval=True)

    registry.register(tool)

    assert registry.get("tool:web_search").requires_approval is True
    assert not hasattr(registry, "execute")
    assert not hasattr(registry, "approve")


def test_tool_definition_is_immutable():
    tool = make_tool()

    with pytest.raises(AttributeError):
        tool.tool_id = "tool:changed"


def test_invalid_schema_type_is_rejected():
    with pytest.raises(TypeError, match="input_schema"):
        make_tool(input_schema=[])


def test_invalid_permission_id_is_rejected():
    with pytest.raises(ValueError, match="permission"):
        make_tool(required_permission_ids=("",))


def test_invalid_supported_tenant_id_is_rejected():
    with pytest.raises(ValueError, match="tenant"):
        make_tool(supported_tenant_ids=("",))
