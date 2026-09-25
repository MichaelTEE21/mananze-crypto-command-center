from dataclasses import dataclass
from typing import Any, Literal
from .risk import RiskLevel

ToolExecutionMode = Literal["internal", "external", "mcp", "sandboxed"]

@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    version: str
    description: str
    capability_id: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    required_permission_ids: tuple[str, ...] = ()
    supported_skill_ids: tuple[str, ...] = ()
    risk: RiskLevel = "low"
    supported_tenant_ids: tuple[str, ...] = ()
    allowed_provider_ids: tuple[str, ...] = ()
    estimated_cost: float = 0.0
    cost_currency: str = "ZAR"
    timeout_seconds: float = 30.0
    max_attempts: int = 1
    execution_mode: ToolExecutionMode = "internal"
    audit_required: bool = True
    requires_approval: bool = False

    def __post_init__(self) -> None:
        for field_name, value in {
            "tool_id": self.tool_id,
            "version": self.version,
            "description": self.description,
            "capability_id": self.capability_id,
            "cost_currency": self.cost_currency,
        }.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")

        if not isinstance(self.input_schema, dict):
            raise TypeError("input_schema must be a dict")
        if not isinstance(self.output_schema, dict):
            raise TypeError("output_schema must be a dict")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        for permission_id in self.required_permission_ids:
            if not isinstance(permission_id, str) or not permission_id.strip():
                raise ValueError("required permission IDs must be non-empty")

        for skill_id in self.supported_skill_ids:
            if not isinstance(skill_id, str) or not skill_id.strip():
                raise ValueError("supported skill IDs must be non-empty")

        for tenant_id in self.supported_tenant_ids:
            if not isinstance(tenant_id, str) or not tenant_id.strip():
                raise ValueError("supported tenant IDs must be non-empty")

        for provider_id in self.allowed_provider_ids:
            if not isinstance(provider_id, str) or not provider_id.strip():
                raise ValueError("allowed provider IDs must be non-empty")


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.tool_id in self._tools:
            raise ValueError(f"tool already registered: {tool.tool_id}")
        self._tools[tool.tool_id] = tool

    def get(self, tool_id: str) -> ToolDefinition:
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError("tool_id is required")
        try:
            return self._tools[tool_id]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {tool_id}") from exc

    def list_all(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._tools.values())

    def tools_for_capability(self, capability_id: str) -> tuple[ToolDefinition, ...]:
        if not isinstance(capability_id, str) or not capability_id.strip():
            raise ValueError("capability_id is required")
        return tuple(
            tool for tool in self._tools.values()
            if tool.capability_id == capability_id
        )

    def supports_tenant(self, tool_id: str, tenant_id: str) -> bool:
        tool = self.get(tool_id)
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not tool.supported_tenant_ids:
            return True
        return tenant_id in tool.supported_tenant_ids

    def supports_provider(self, tool_id: str, provider_id: str) -> bool:
        tool = self.get(tool_id)
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id is required")
        if not tool.allowed_provider_ids:
            return True
        return provider_id in tool.allowed_provider_ids


__all__ = ["ToolDefinition", "ToolExecutionMode", "ToolRegistry"]
