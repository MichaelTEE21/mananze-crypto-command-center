"""Governed boundary between bound tools and provider execution."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.governed_execution import GovernedExecutionResult
from mananze_os.governed_provider_execution import (
    GovernedProviderExecutionBoundary,
    GovernedProviderExecutionResult,
)
from mananze_os.tool_registry import ToolRegistry
from mananze_os.tool_selection import ToolBinding, ToolBindingPlan


@dataclass(frozen=True)
class GovernedToolExecutionResult:
    governance: GovernedExecutionResult
    binding: ToolBinding
    provider: GovernedProviderExecutionResult

    @property
    def success(self) -> bool:
        return self.provider.success


class GovernedToolExecutionBoundary:
    """
    Final governance check between a bound execution graph and provider runtime.

    This boundary:
    - does not select tools
    - does not select providers
    - does not grant authority
    - does not approve actions
    - does not execute providers directly

    It verifies the exact tool binding and execution lineage, then delegates
    provider execution to GovernedProviderExecutionBoundary.
    """

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        provider_boundary: GovernedProviderExecutionBoundary,
    ) -> None:
        if not isinstance(tool_registry, ToolRegistry):
            raise TypeError("tool_registry must be ToolRegistry")

        if not isinstance(
            provider_boundary,
            GovernedProviderExecutionBoundary,
        ):
            raise TypeError(
                "provider_boundary must be GovernedProviderExecutionBoundary"
            )

        self.tool_registry = tool_registry
        self.provider_boundary = provider_boundary

    def execute(
        self,
        *,
        plan: ToolBindingPlan,
        governance: GovernedExecutionResult,
    ) -> GovernedToolExecutionResult:
        if not isinstance(plan, ToolBindingPlan):
            raise TypeError("plan must be ToolBindingPlan")

        if not isinstance(governance, GovernedExecutionResult):
            raise TypeError(
                "governance must be GovernedExecutionResult"
            )

        if not governance.allowed:
            raise PermissionError(
                "governed execution is not allowed"
            )

        action_request = governance.action_request
        if action_request is None:
            raise ValueError(
                "governed execution has no action request"
            )

        if governance.tenant_id != plan.tenant_id:
            raise ValueError(
                "governance tenant does not match tool binding plan"
            )

        if governance.work_order_id != plan.work_order_id:
            raise ValueError(
                "governance work order does not match tool binding plan"
            )

        binding = self._resolve_binding(
            plan=plan,
            governance=governance,
        )

        self._validate_execution_node(
            plan=plan,
            governance=governance,
            binding=binding,
        )

        self._validate_registered_tool(
            binding=binding,
            tenant_id=plan.tenant_id,
        )

        self._validate_governance(
            governance=governance,
            binding=binding,
        )

        provider_result = self.provider_boundary.execute(
            governance
        )

        return GovernedToolExecutionResult(
            governance=governance,
            binding=binding,
            provider=provider_result,
        )

    @staticmethod
    def _resolve_binding(
        *,
        plan: ToolBindingPlan,
        governance: GovernedExecutionResult,
    ) -> ToolBinding:
        matches = tuple(
            binding
            for binding in plan.bindings
            if binding.capability_id == governance.capability_id
            and binding.tenant_id == plan.tenant_id
        )

        if not matches:
            raise ValueError(
                "no tool binding exists for governed capability"
            )

        if len(matches) != 1:
            raise ValueError(
                "multiple tool bindings exist for governed capability"
            )

        return matches[0]

    @staticmethod
    def _validate_execution_node(
        *,
        plan: ToolBindingPlan,
        governance: GovernedExecutionResult,
        binding: ToolBinding,
    ) -> None:
        nodes = tuple(
            node
            for node in plan.execution_graph.nodes
            if node.capability_id == governance.capability_id
        )

        if not nodes:
            raise ValueError(
                "no execution node exists for governed capability"
            )

        if len(nodes) != 1:
            raise ValueError(
                "multiple execution nodes exist for governed capability"
            )

        node = nodes[0]

        if node.tool_id is None:
            raise ValueError(
                "execution node has no bound tool"
            )

        if node.tool_id != binding.tool_id:
            raise ValueError(
                "execution node tool does not match tool binding"
            )

    def _validate_registered_tool(
        self,
        *,
        binding: ToolBinding,
        tenant_id: str,
    ) -> None:
        try:
            tool = self.tool_registry.get(binding.tool_id)
        except KeyError as exc:
            raise LookupError(
                f"tool not registered: {binding.tool_id}"
            ) from exc

        if tool.capability_id != binding.capability_id:
            raise ValueError(
                "registered tool capability does not match tool binding"
            )

        if not self.tool_registry.supports_tenant(
            binding.tool_id,
            tenant_id,
        ):
            raise PermissionError(
                "registered tool does not support tenant"
            )

        if tool.execution_mode != binding.execution_mode:
            raise ValueError(
                "registered tool execution mode does not match binding"
            )

        if tool.risk != binding.risk:
            raise ValueError(
                "registered tool risk does not match binding"
            )

        if tuple(tool.required_permission_ids) != tuple(
            binding.required_permission_ids
        ):
            raise ValueError(
                "registered tool permissions do not match binding"
            )

        if tuple(tool.supported_skill_ids) != tuple(
            binding.supported_skill_ids
        ):
            raise ValueError(
                "registered tool skills do not match binding"
            )

        if tuple(tool.allowed_provider_ids) != tuple(
            binding.allowed_provider_ids
        ):
            raise ValueError(
                "registered tool provider restrictions do not match binding"
            )

    @staticmethod
    def _validate_governance(
        *,
        governance: GovernedExecutionResult,
        binding: ToolBinding,
    ) -> None:
        request = governance.action_request

        if request is None:
            raise ValueError(
                "governance has no action request"
            )

        if request.execution_id != governance.execution_id:
            raise ValueError(
                "action execution does not match governance execution"
            )

        if request.tenant_id != governance.tenant_id:
            raise ValueError(
                "action tenant does not match governance tenant"
            )

        if request.capability_id != binding.capability_id:
            raise ValueError(
                "action capability does not match tool binding"
            )

        if request.tool_id != binding.tool_id:
            raise ValueError(
                "action tool does not match tool binding"
            )


