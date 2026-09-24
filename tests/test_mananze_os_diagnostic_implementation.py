from mananze_os.diagnostic import (
    BusinessDiagnostic,
    DiagnosticReport,
    ImplementationScope,
)
from mananze_os.diagnostic_implementation import DiagnosticImplementationBridge
from mananze_os.input_request import InputRequest


def make_scope(
    *,
    tenant_id: str = "tenant-1",
    objective: str = "Improve business operations",
) -> ImplementationScope:
    return ImplementationScope(
        tenant_id=tenant_id,
        objective=objective,
        recommended_capability_ids=("operations", "reporting"),
        required_domains=("business",),
        integration_requirements=(),
        risks=(),
        dependencies=(),
        estimated_complexity="low",
    )


def make_request(
    *,
    tenant_id: str = "tenant-1",
    objective: str = "Improve business operations",
) -> InputRequest:
    return InputRequest(
        request_id="request-1",
        tenant_id=tenant_id,
        actor_id="client-owner",
        objective=objective,
    )


def test_accepted_scope_compiles_through_existing_pipeline() -> None:
    bridge = DiagnosticImplementationBridge()

    result = bridge.compile_accepted_scope(
        scope=make_scope(),
        request=make_request(),
    )

    assert result.work_order.tenant_id == "tenant-1"
    assert result.work_order.objective == "Improve business operations"

    assert result.compiled_plan.work_order_id == "request-1"
    assert result.compiled_plan.tenant_id == "tenant-1"

    assert tuple(
        requirement.capability_id
        for requirement in result.compiled_plan.requirements
    ) == ("operations", "reporting")

    assert result.workforce_plan.work_order_id == "request-1"
    assert result.workforce_plan.objective == "Improve business operations"


def test_scope_recommendations_remain_advisory_to_compiler() -> None:
    scope = ImplementationScope(
        tenant_id="tenant-1",
        objective="Improve business operations",
        recommended_capability_ids=("sales",),
        required_domains=("business",),
        integration_requirements=(),
        risks=(),
        dependencies=(),
        estimated_complexity="low",
    )

    result = DiagnosticImplementationBridge().compile_accepted_scope(
        scope=scope,
        request=make_request(),
    )

    compiled_capabilities = tuple(
        requirement.capability_id
        for requirement in result.compiled_plan.requirements
    )

    assert compiled_capabilities == ("operations", "reporting")
    assert scope.recommended_capability_ids == ("sales",)


def test_cross_tenant_scope_is_rejected() -> None:
    bridge = DiagnosticImplementationBridge()

    try:
        bridge.compile_accepted_scope(
            scope=make_scope(tenant_id="tenant-a"),
            request=make_request(tenant_id="tenant-b"),
        )
    except PermissionError as exc:
        assert "tenant_id" in str(exc)
    else:
        raise AssertionError("expected cross-tenant scope rejection")


def test_objective_mismatch_is_rejected() -> None:
    bridge = DiagnosticImplementationBridge()

    try:
        bridge.compile_accepted_scope(
            scope=make_scope(objective="Improve business operations"),
            request=make_request(objective="Run marketing campaign"),
        )
    except ValueError as exc:
        assert "objective" in str(exc)
    else:
        raise AssertionError("expected objective mismatch rejection")


def test_bridge_does_not_approve_or_execute() -> None:
    result = DiagnosticImplementationBridge().compile_accepted_scope(
        scope=make_scope(),
        request=make_request(),
    )

    assert result.work_order.status == "planned"
