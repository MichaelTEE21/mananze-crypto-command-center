"""Central Provider Execution Gateway.

All external provider execution must cross this boundary.

The gateway enforces tool/provider/tenant execution constraints and records
provider health, usage, latency, and cost observations.

It does not grant authority. Policy, authorization, ActionGate,
and human approval remain upstream authorities.
"""

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from .provider import ProviderRequest, ProviderResponse
from .provider_observability import ProviderHealthRegistry, ProviderUsageLedger
from .provider_registry import ProviderRegistry
from .tool_registry import ToolDefinition, ToolRegistry


@dataclass(frozen=True)
class GatewayResult:
    success: bool
    provider_id: str
    tool_id: str
    tenant_id: str
    execution_id: str
    output: dict[str, Any]
    error: str | None = None
    usage: dict[str, Any] | None = None
    cost: float = 0.0
    cost_currency: str = "ZAR"


class ProviderExecutionGateway:
    """Controlled boundary between Mananze execution and external providers."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        provider_registry: ProviderRegistry,
        *,
        health_registry: ProviderHealthRegistry | None = None,
        usage_ledger: ProviderUsageLedger | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.provider_registry = provider_registry
        self.health_registry = health_registry
        self.usage_ledger = usage_ledger

    @staticmethod
    def _validate_required_fields(
        *,
        provider_id: str,
        tool_id: str,
        tenant_id: str,
        execution_id: str,
        operation: str,
    ) -> None:
        fields = {
            "provider_id": provider_id,
            "tool_id": tool_id,
            "tenant_id": tenant_id,
            "execution_id": execution_id,
            "operation": operation,
        }

        for name, value in fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")

    @staticmethod
    def _validate_tool_configuration(tool: ToolDefinition) -> None:
        if tool.timeout_seconds <= 0:
            raise ValueError(
                f"tool {tool.tool_id} has invalid timeout configuration"
            )

        if tool.max_attempts < 1:
            raise ValueError(
                f"tool {tool.tool_id} has invalid retry configuration"
            )

        if tool.estimated_cost < 0:
            raise ValueError(
                f"tool {tool.tool_id} has invalid estimated cost"
            )

    def _record_observation(
        self,
        *,
        provider_id: str,
        tool_id: str,
        tenant_id: str,
        execution_id: str,
        success: bool,
        latency_ms: float,
        usage: dict[str, Any] | None,
        cost: float,
        cost_currency: str,
    ) -> None:
        if self.health_registry is not None:
            self.health_registry.record(
                provider_id=provider_id,
                success=success,
                latency_ms=latency_ms,
            )

        if self.usage_ledger is not None:
            self.usage_ledger.record(
                provider_id=provider_id,
                tool_id=tool_id,
                tenant_id=tenant_id,
                execution_id=execution_id,
                success=success,
                latency_ms=latency_ms,
                usage=usage,
                cost=cost,
                cost_currency=cost_currency,
            )

    def execute(
        self,
        *,
        provider_id: str,
        tool_id: str,
        tenant_id: str,
        execution_id: str,
        operation: str,
        payload: dict[str, Any],
    ) -> GatewayResult:
        """Execute a registered tool through a registered provider.

        This method intentionally does not perform authorization or approval.
        Those decisions belong to the upstream Mananze control plane.
        """

        self._validate_required_fields(
            provider_id=provider_id,
            tool_id=tool_id,
            tenant_id=tenant_id,
            execution_id=execution_id,
            operation=operation,
        )

        self._validate_payload(payload)

        tool = self.tool_registry.get(tool_id)
        self._validate_tool_configuration(tool)

        if not self.tool_registry.supports_tenant(tool_id, tenant_id):
            raise PermissionError(
                f"tool {tool_id} is not supported for tenant {tenant_id}"
            )

        if not self.tool_registry.supports_provider(tool_id, provider_id):
            raise PermissionError(
                f"provider {provider_id} is not allowed for tool {tool_id}"
            )

        provider = self.provider_registry.get(provider_id)

        request = ProviderRequest(
            provider_id=provider_id,
            tool_id=tool.tool_id,
            tenant_id=tenant_id,
            execution_id=execution_id,
            operation=operation,
            payload=payload,
            timeout_seconds=tool.timeout_seconds,
        )

        started = perf_counter()

        try:
            response: ProviderResponse = provider.execute(request)
            latency_ms = (perf_counter() - started) * 1000

            if response.provider_id != provider_id:
                raise RuntimeError("provider returned a mismatched provider ID")

            if response.tool_id != tool_id:
                raise RuntimeError("provider returned a mismatched tool ID")

            if response.tenant_id != tenant_id:
                raise RuntimeError("provider returned a cross-tenant response")

            if response.execution_id != execution_id:
                raise RuntimeError(
                    "provider returned a mismatched execution ID"
                )

            if not isinstance(response.output, dict):
                raise TypeError("provider response output must be a dict")

            if response.cost < 0:
                raise ValueError("provider response cost cannot be negative")

            if (
                not isinstance(response.cost_currency, str)
                or not response.cost_currency.strip()
            ):
                raise ValueError(
                    "provider response cost currency is required"
                )

            self._record_observation(
                provider_id=provider_id,
                tool_id=tool_id,
                tenant_id=tenant_id,
                execution_id=execution_id,
                success=response.success,
                latency_ms=latency_ms,
                usage=response.usage,
                cost=response.cost,
                cost_currency=response.cost_currency,
            )

            return GatewayResult(
                success=response.success,
                provider_id=response.provider_id,
                tool_id=response.tool_id,
                tenant_id=response.tenant_id,
                execution_id=response.execution_id,
                output=response.output,
                error=response.error,
                usage=response.usage,
                cost=response.cost,
                cost_currency=response.cost_currency,
            )

        except Exception:
            latency_ms = (perf_counter() - started) * 1000

            self._record_observation(
                provider_id=provider_id,
                tool_id=tool_id,
                tenant_id=tenant_id,
                execution_id=execution_id,
                success=False,
                latency_ms=latency_ms,
                usage=None,
                cost=0.0,
                cost_currency="ZAR",
            )

            raise


__all__ = ["GatewayResult", "ProviderExecutionGateway"]

