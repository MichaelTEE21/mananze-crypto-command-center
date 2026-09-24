"""Mananze Platform -> Hub -> OS capability integration tests."""

from mananze_os.authority import Authority
from mananze_os.permission import CapabilityPermission
from mananze_os.runtime import MananzeRuntime
from mananze_os.tenant import Tenant
from mananze_platform.capability_discovery import (
    discover_capabilities,
    resolve_os_capability_candidates,
)
from mananze_platform.intake import (
    BusinessIntake,
    IntakeSource,
    analyse_intake,
)
from mananze_platform.runtime_adapter import (
    PlatformRuntimeRequest,
    prepare_platform_request,
    to_input_request,
)


def test_business_intake_discovers_and_compiles_os_capabilities():
    tenant = Tenant(
        tenant_id="tenant:transport-test",
        name="Transport Test",
        active=True,
    )

    authority = Authority(
        actor_id="actor:owner",
        level="human",
        can_execute=True,
        requires_approval=True,
    )

    intake = BusinessIntake(
        tenant_id=tenant.tenant_id,
        actor_id=authority.actor_id,
        source=IntakeSource.BUSINESS_DESCRIPTION,
        content=(
            "We run a transport business and need more customers, "
            "better sales, deliveries and fleet operations."
        ),
    )

    analysis = analyse_intake(intake)
    candidates = discover_capabilities(analysis.observations)
    os_capability_ids = resolve_os_capability_candidates(candidates)

    assert os_capability_ids == (
        "marketing",
        "sales",
        "revenue",
        "logistics",
        "fleet",
        "cost_analysis",
        "reporting",
    )

    request = PlatformRuntimeRequest(
        tenant=tenant,
        authority=authority,
        intake=intake,
        objective=intake.content,
        capability_candidates=candidates,
    )

    input_request = to_input_request(request)

    assert input_request.candidate_capability_ids == os_capability_ids

    permissions = tuple(
        CapabilityPermission(
            actor_id=authority.actor_id,
            tenant_id=tenant.tenant_id,
            capability_id=capability_id,
            allowed=True,
        )
        for capability_id in os_capability_ids
    )

    runtime = MananzeRuntime(
        tenants=(tenant,),
        authorities=(authority,),
        permissions=permissions,
    )

    result = prepare_platform_request(runtime, request)

    compiled_ids = tuple(
        requirement.capability_id
        for requirement in result.plan.requirements
    )

    assert compiled_ids == os_capability_ids

    workforce_ids = tuple(
        role.capability_id
        for role in result.workforce.roles
    )

    assert workforce_ids == os_capability_ids

    assert result.authorization.allowed is True


