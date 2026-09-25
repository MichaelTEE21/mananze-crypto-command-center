from mananze_os.composition import build_runtime
from mananze_os.runtime import RuntimeExecutionBoundary
from mananze_os.tool_catalog import default_tool_registry


def test_composition_uses_authoritative_tool_catalog():
    runtime = build_runtime()

    assert runtime.provider_router is not None
    assert runtime.provider_router.tool_registry.list_all() == (
        default_tool_registry().list_all()
    )


def test_composition_wires_runtime_provider_boundary():
    runtime = build_runtime()

    assert runtime.provider_router is not None
    assert isinstance(
        runtime.runtime_execution_boundary,
        RuntimeExecutionBoundary,
    )
    assert runtime.runtime_execution_boundary.router is runtime.provider_router
