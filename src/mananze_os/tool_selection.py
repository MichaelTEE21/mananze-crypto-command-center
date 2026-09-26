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


from dataclasses import replace
from typing import Iterable

from .capability_workforce_bridge import CapabilityWorkforcePlan


@dataclass(frozen=True)
class ToolBinding:
    """Authoritative binding between an execution node and a registered tool."""

    node_id: str
    capability_id: str
    tool_id: str
    tenant_id: str
    execution_mode: str
    risk: str
    required_permission_ids: tuple[str, ...] = ()
    supported_skill_ids: tuple[str, ...] = ()
    allowed_provider_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "node_id",
            "capability_id",
            "tool_id",
            "tenant_id",
            "execution_mode",
            "risk",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} cannot be blank")


@dataclass(frozen=True)
class ToolBindingPlan:
    """Execution graph after every node has a governed tool binding."""

    tenant_id: str
    twin_id: str
    work_order_id: str
    bindings: tuple[ToolBinding, ...]
    execution_graph: object

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be blank")
        if not self.twin_id.strip():
            raise ValueError("twin_id cannot be blank")
        if not self.work_order_id.strip():
            raise ValueError("work_order_id cannot be blank")

        node_ids = tuple(binding.node_id for binding in self.bindings)
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("duplicate tool binding node_id")

    @property
    def tool_ids(self) -> tuple[str, ...]:
        return tuple(binding.tool_id for binding in self.bindings)

    def binding_for_node(self, node_id: str) -> ToolBinding:
        for binding in self.bindings:
            if binding.node_id == node_id:
                return binding
        raise KeyError(node_id)


class ToolSelectionEngine:
    """
    Bind execution nodes to authoritative registered tools.

    This layer selects and binds tools only. It does not grant authority,
    approve actions, execute tools, or route providers.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def bind(
        self,
        plan: CapabilityWorkforcePlan,
        *,
        granted_permission_ids: Iterable[str] = (),
        available_provider_ids: Iterable[str] = (),
    ) -> ToolBindingPlan:
        if not isinstance(plan, CapabilityWorkforcePlan):
            raise TypeError("plan must be a CapabilityWorkforcePlan")

        granted_permissions = {
            permission_id.strip()
            for permission_id in granted_permission_ids
            if isinstance(permission_id, str) and permission_id.strip()
        }

        available_providers = {
            provider_id.strip()
            for provider_id in available_provider_ids
            if isinstance(provider_id, str) and provider_id.strip()
        }

        bindings: list[ToolBinding] = []
        graph_nodes = []

        for node in plan.execution_graph.nodes:
            if node.tool_id is not None:
                raise ValueError(
                    f"execution node is already bound to a tool: {node.node_id}"
                )

            candidate_tools = tuple(
                tool
                for tool in self.registry.tools_for_capability(
                    node.capability_id
                )
                if self._eligible(
                    tool,
                    tenant_id=plan.tenant_id,
                    required_skill_ids=node.skill_ids,
                    granted_permission_ids=granted_permissions,
                    available_provider_ids=available_providers,
                )
            )

            if not candidate_tools:
                raise LookupError(
                    f"no eligible tool for execution node: {node.node_id}"
                )

            selected = self._select(candidate_tools)

            bindings.append(
                ToolBinding(
                    node_id=node.node_id,
                    capability_id=node.capability_id,
                    tool_id=selected.tool_id,
                    tenant_id=plan.tenant_id,
                    execution_mode=selected.execution_mode,
                    risk=selected.risk,
                    required_permission_ids=selected.required_permission_ids,
                    supported_skill_ids=selected.supported_skill_ids,
                    allowed_provider_ids=selected.allowed_provider_ids,
                )
            )

            graph_nodes.append(replace(node, tool_id=selected.tool_id))

        bound_graph = replace(
            plan.execution_graph,
            nodes=tuple(graph_nodes),
        )

        return ToolBindingPlan(
            tenant_id=plan.tenant_id,
            twin_id=plan.twin_id,
            work_order_id=plan.work_order_id,
            bindings=tuple(bindings),
            execution_graph=bound_graph,
        )

    @staticmethod
    def _eligible(
        tool: ToolDefinition,
        *,
        tenant_id: str,
        required_skill_ids: tuple[str, ...],
        granted_permission_ids: set[str],
        available_provider_ids: set[str],
    ) -> bool:
        if not _tool_supports_tenant(tool, tenant_id):
            return False

        if not set(required_skill_ids).issubset(
            set(tool.supported_skill_ids)
        ):
            return False

        if not set(tool.required_permission_ids).issubset(
            granted_permission_ids
        ):
            return False

        if (
            tool.allowed_provider_ids
            and available_provider_ids
            and not (
                set(tool.allowed_provider_ids)
                & available_provider_ids
            )
        ):
            return False

        return True

    @staticmethod
    def _select(tools: tuple[ToolDefinition, ...]) -> ToolDefinition:
        """Select deterministically among eligible tools."""
        return min(
            tools,
            key=lambda tool: (
                _risk_order(tool.risk),
                tool.estimated_cost,
                tool.tool_id,
                tool.version,
            ),
        )


def _tool_supports_tenant(
    tool: ToolDefinition,
    tenant_id: str,
) -> bool:
    if not tool.supported_tenant_ids:
        return True

    return tenant_id in tool.supported_tenant_ids


def _risk_order(risk: str) -> int:
    return {
        "low": 0,
        "medium": 1,
        "high": 2,
        "critical": 3,
    }.get(risk, 99)


__all__ = [
    "ToolSelection",
    "ToolSelector",
    "ToolBinding",
    "ToolBindingPlan",
    "ToolSelectionEngine",
]
