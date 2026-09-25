"""Authoritative MANANZE OS capability-to-tool selection.

Tool selection is a planning concern. It does not execute tools, grant
authority, approve actions, or route providers.
"""

from dataclasses import dataclass

from .tool_registry import ToolDefinition, ToolRegistry


@dataclass(frozen=True)
class ToolSelection:
    capability_id: str
    tool_id: str


class ToolSelector:
    """Select an eligible OS tool for a compiled capability."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def select(
        self,
        capability_id: str,
        *,
        objective: str = "",
        required_skill_ids: tuple[str, ...] = (),
        preferred_tool_id: str | None = None,
    ) -> ToolSelection:
        tools = tuple(
            tool
            for tool in self.registry.tools_for_capability(capability_id)
            if all(
                permission_id.strip()
                for permission_id in tool.required_permission_ids
            )
        )

        if not tools:
            raise ValueError(
                f"no registered tool available for capability: {capability_id}"
            )

        if preferred_tool_id is not None:
            if not isinstance(preferred_tool_id, str) or not preferred_tool_id.strip():
                raise ValueError("preferred_tool_id cannot be blank")

            preferred = self.registry.get(preferred_tool_id)

            if preferred.capability_id != capability_id:
                raise ValueError(
                    f"preferred tool does not belong to capability: "
                    f"{capability_id}"
                )

            if preferred not in tools:
                raise ValueError(
                    f"preferred tool is not eligible for capability: "
                    f"{capability_id}"
                )

            return ToolSelection(
                capability_id=capability_id,
                tool_id=preferred.tool_id,
            )

        # Use declared workforce skills as the primary deterministic
        # selection signal. This keeps tool selection tied to the
        # compiled workforce plan rather than guessing from prose.
        skill_matches = tuple(
            tool
            for tool in tools
            if _skills_match_tool(required_skill_ids, tool)
        )

        if len(skill_matches) == 1:
            return ToolSelection(
                capability_id=capability_id,
                tool_id=skill_matches[0].tool_id,
            )

        # Objective matching remains a secondary signal for cases where
        # skills do not uniquely identify the operation.
        normalized = objective.casefold()
        objective_matches = tuple(
            tool
            for tool in tools
            if _objective_matches_tool(normalized, tool)
        )

        if len(objective_matches) == 1:
            return ToolSelection(
                capability_id=capability_id,
                tool_id=objective_matches[0].tool_id,
            )

        if len(tools) == 1:
            return ToolSelection(
                capability_id=capability_id,
                tool_id=tools[0].tool_id,
            )

        if len(skill_matches) > 1 or len(objective_matches) > 1:
            raise ValueError(
                f"ambiguous tool selection for capability: {capability_id}"
            )

        raise ValueError(
            f"objective does not identify a unique tool for capability: "
            f"{capability_id}"
        )


def _skills_match_tool(
    required_skill_ids: tuple[str, ...],
    tool: ToolDefinition,
) -> bool:
    """Match only against explicitly declared tool skill metadata."""

    if not required_skill_ids:
        return False

    required = {
        skill_id.strip()
        for skill_id in required_skill_ids
        if isinstance(skill_id, str) and skill_id.strip()
    }

    supported = set(tool.supported_skill_ids)

    return bool(required) and required.issubset(supported)

def _objective_matches_tool(
    objective: str,
    tool: ToolDefinition,
) -> bool:
    tool_text = (
        f"{tool.tool_id} "
        f"{tool.description}"
    ).casefold()

    keyword_groups = {
        "campaign": ("campaign",),
        "content": ("content", "copy", "post"),
        "lead": ("lead", "prospect", "qualification"),
        "qualif": ("qualification",),
        "follow": ("follow",),
        "revenue": ("revenue",),
        "route": ("route", "delivery", "transport"),
        "fleet": ("fleet", "vehicle"),
        "cost": ("cost", "expense"),
        "report": ("report",),
        "message": ("message", "communication", "customer"),
        "workflow": ("workflow", "operations"),
    }

    return any(
        any(keyword in objective for keyword in keywords)
        and any(keyword in tool_text for keyword in keywords)
        for keywords in keyword_groups.values()
    )


__all__ = ["ToolSelection", "ToolSelector"]
