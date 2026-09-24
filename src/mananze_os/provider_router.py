"""Deterministic provider routing with controlled fallback.

The router chooses only from explicitly configured providers.
It does not grant authority and must never bypass the ProviderExecutionGateway.
"""

from dataclasses import dataclass
from typing import Any

from .provider_gateway import GatewayResult, ProviderExecutionGateway
from .provider_registry import ProviderRegistry
from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class ProviderRoute:
    tool_id: str
    primary_provider_id: str
    fallback_provider_ids: tuple[str, ...] = ()
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.tool_id, str) or not self.tool_id.strip():
            raise ValueError("tool_id is required")

        if (
            not isinstance(self.primary_provider_id, str)
            or not self.primary_provider_id.strip()
        ):
            raise ValueError("primary_provider_id is required")

        for provider_id in self.fallback_provider_ids:
            if not isinstance(provider_id, str) or not provider_id.strip():
                raise ValueError("fallback provider IDs must be non-empty")

        if self.primary_provider_id in self.fallback_provider_ids:
            raise ValueError(
                "primary provider cannot also be configured as a fallback"
            )

        if len(set(self.fallback_provider_ids)) != len(
            self.fallback_provider_ids
        ):
            raise ValueError("fallback provider IDs must be unique")


@dataclass(frozen=True)
class ProviderRoutingResult:
    success: bool
    provider_id: str | None
    tool_id: str
    tenant_id: str
    execution_id: str
    output: dict[str, Any]
    error: str | None = None
    usage: dict[str, Any] | None = None
    cost: float = 0.0
    cost_currency: str = "ZAR"
    attempted_provider_ids: tuple[str, ...] = ()


class ProviderRouter:
    """Selects an explicitly configured provider route.

    Authority remains upstream. Actual provider execution always crosses
    ProviderExecutionGateway.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        provider_registry: ProviderRegistry,
        gateway: ProviderExecutionGateway,
        routes: tuple[ProviderRoute, ...] = (),
    ) -> None:
        self.tool_registry = tool_registry
        self.provider_registry = provider_registry
        self.gateway = gateway
        self._routes: dict[str, ProviderRoute] = {}

        for route in routes:
            self.register_route(route)

    def register_route(self, route: ProviderRoute) -> None:
        if route.tool_id in self._routes:
            raise ValueError(f"route already registered: {route.tool_id}")

        self.tool_registry.get(route.tool_id)

        configured_provider_ids = (
            route.primary_provider_id,
            *route.fallback_provider_ids,
        )

        for provider_id in configured_provider_ids:
            if not self.tool_registry.supports_provider(
                route.tool_id, provider_id
            ):
                raise PermissionError(
                    f"provider {provider_id} is not allowed for tool "
                    f"{route.tool_id}"
                )

        self._routes[route.tool_id] = route

    def get_route(self, tool_id: str) -> ProviderRoute:
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError("tool_id is required")

        try:
            return self._routes[tool_id]
        except KeyError as exc:
            raise KeyError(f"unknown provider route: {tool_id}") from exc

    def route(
        self,
        *,
        tool_id: str,
        tenant_id: str,
        execution_id: str,
        operation: str,
        payload: dict[str, Any],
    ) -> ProviderRoutingResult:
        route = self.get_route(tool_id)

        if not route.enabled:
            raise PermissionError(
                f"provider route is disabled for tool {tool_id}"
            )

        candidates = (
            route.primary_provider_id,
            *route.fallback_provider_ids,
        )

        attempted: list[str] = []
        failures: list[str] = []

        for provider_id in candidates:
            attempted.append(provider_id)

            try:
                # The router may select a provider, but execution MUST
                # always cross the central gateway.
                self.provider_registry.get(provider_id)

                if not self.tool_registry.supports_provider(
                    tool_id, provider_id
                ):
                    failures.append(
                        f"{provider_id}: provider not allowed for tool"
                    )
                    continue

                result: GatewayResult = self.gateway.execute(
                    provider_id=provider_id,
                    tool_id=tool_id,
                    tenant_id=tenant_id,
                    execution_id=execution_id,
                    operation=operation,
                    payload=payload,
                )

            except (KeyError, PermissionError, ValueError, TypeError) as exc:
                failures.append(f"{provider_id}: {exc}")
                continue

            if result.success:
                return ProviderRoutingResult(
                    success=True,
                    provider_id=result.provider_id,
                    tool_id=result.tool_id,
                    tenant_id=result.tenant_id,
                    execution_id=result.execution_id,
                    output=result.output,
                    error=result.error,
                    usage=result.usage,
                    cost=result.cost,
                    cost_currency=result.cost_currency,
                    attempted_provider_ids=tuple(attempted),
                )

            failures.append(
                f"{provider_id}: {result.error or 'provider execution failed'}"
            )

        error = (
            f"all configured providers failed for tool {tool_id}; "
            f"attempted={tuple(attempted)}; "
            f"failures={tuple(failures)}"
        )

        return ProviderRoutingResult(
            success=False,
            provider_id=None,
            tool_id=tool_id,
            tenant_id=tenant_id,
            execution_id=execution_id,
            output={},
            error=error,
            attempted_provider_ids=tuple(attempted),
        )


__all__ = ["ProviderRoute", "ProviderRoutingResult", "ProviderRouter"]
