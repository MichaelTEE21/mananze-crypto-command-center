import pytest

from mananze_os.tool_catalog import default_tool_registry
from mananze_os.tool_selection import ToolSelector


def test_single_tool_capability_selects_authoritative_tool():
    selector = ToolSelector(default_tool_registry())

    selection = selector.select(
        "logistics",
        objective="Plan deliveries and transport routes",
    )

    assert selection.capability_id == "logistics"
    assert selection.tool_id == "mananze:logistics:route_plan"


def test_multiple_tools_use_objective_to_select_tool():
    selector = ToolSelector(default_tool_registry())

    campaign = selector.select(
        "marketing",
        objective="Create a marketing campaign",
    )

    content = selector.select(
        "marketing",
        objective="Create marketing content",
    )

    assert campaign.tool_id == "mananze:marketing:campaign_plan"
    assert content.tool_id == "mananze:marketing:content_draft"


def test_ambiguous_multiple_tool_capability_fails_closed():
    selector = ToolSelector(default_tool_registry())

    with pytest.raises(ValueError, match="objective does not identify"):
        selector.select(
            "marketing",
            objective="Help with marketing",
        )


def test_selector_accepts_valid_preferred_tool() -> None:
    registry = default_tool_registry()
    selector = ToolSelector(registry)

    selection = selector.select(
        "marketing",
        preferred_tool_id="mananze:marketing:content_draft",
    )

    assert selection.capability_id == "marketing"
    assert selection.tool_id == "mananze:marketing:content_draft"


def test_selector_rejects_preferred_tool_from_different_capability() -> None:
    registry = default_tool_registry()
    selector = ToolSelector(registry)

    with pytest.raises(ValueError, match="does not belong to capability"):
        selector.select(
            "marketing",
            preferred_tool_id="mananze:sales:lead_qualification",
        )


def test_selector_rejects_unknown_preferred_tool() -> None:
    registry = default_tool_registry()
    selector = ToolSelector(registry)

    with pytest.raises(KeyError):
        selector.select(
            "marketing",
            preferred_tool_id="mananze:missing:tool",
        )
