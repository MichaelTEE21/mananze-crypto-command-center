from mananze_os.tool_catalog import default_tool_registry
from mananze_os.tool_selection import ToolSelector


def test_marketing_campaign_skill_selects_campaign_tool():
    selector = ToolSelector(default_tool_registry())

    result = selector.select(
        "marketing",
        required_skill_ids=("marketing:campaign_planning",),
    )

    assert result.tool_id == "mananze:marketing:campaign_plan"


def test_marketing_content_skill_selects_content_tool():
    selector = ToolSelector(default_tool_registry())

    result = selector.select(
        "marketing",
        required_skill_ids=("marketing:content_creation",),
    )

    assert result.tool_id == "mananze:marketing:content_draft"


def test_sales_qualification_skill_selects_qualification_tool():
    selector = ToolSelector(default_tool_registry())

    result = selector.select(
        "sales",
        required_skill_ids=("sales:lead_qualification",),
    )

    assert result.tool_id == "mananze:sales:lead_qualification"


def test_sales_follow_up_skill_selects_follow_up_tool():
    selector = ToolSelector(default_tool_registry())

    result = selector.select(
        "sales",
        required_skill_ids=("sales:follow_up",),
    )

    assert result.tool_id == "mananze:sales:follow_up_plan"


def test_unknown_skill_does_not_guess_between_tools():
    selector = ToolSelector(default_tool_registry())

    try:
        selector.select(
            "marketing",
            required_skill_ids=("unknown:skill",),
        )
    except ValueError as exc:
        assert "objective does not identify" in str(exc)
    else:
        raise AssertionError(
            "ToolSelector guessed a tool without explicit skill metadata."
        )
