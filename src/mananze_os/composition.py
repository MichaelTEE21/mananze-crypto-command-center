"""Canonical MANANZE OS application composition.

This module wires existing authoritative OS components together.
It does not introduce execution, authorization, approval, or orchestration logic.
"""

from mananze_os.provider_gateway import ProviderExecutionGateway
from mananze_os.provider_registry import ProviderRegistry
from mananze_os.provider_router import ProviderRoute, ProviderRouter
from mananze_os.runtime import MananzeRuntime
from mananze_os.tool_catalog import default_tool_registry


def build_runtime(
    *,
    tenants=(),
    authorities=(),
    permissions=(),
    task_store=None,
    provider_registry=None,
    provider_routes=(),
):
    """Build a MANANZE runtime from the authoritative infrastructure.

    Providers and routes are explicitly supplied by the application boundary.
    No provider credentials or external integrations are created here.
    """

    tool_registry = default_tool_registry()
    provider_registry = provider_registry or ProviderRegistry()

    gateway = ProviderExecutionGateway(
        tool_registry=tool_registry,
        provider_registry=provider_registry,
    )

    router = ProviderRouter(
        tool_registry=tool_registry,
        provider_registry=provider_registry,
        gateway=gateway,
        routes=tuple(provider_routes),
    )

    return MananzeRuntime(
        tenants=tenants,
        authorities=authorities,
        permissions=permissions,
        task_store=task_store,
        provider_router=router,
    )
