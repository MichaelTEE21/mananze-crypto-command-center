import pytest

from mananze_os.authority import Authority
from mananze_os.authorization import AuthorizationEngine
from mananze_os.permission import CapabilityPermission
from mananze_os.tenant import Tenant
from mananze_os.workforce_planner import WorkforcePlanner


@pytest.fixture
def planner() -> WorkforcePlanner:
    return WorkforcePlanner()


@pytest.fixture
def tenant() -> Tenant:
    return Tenant(
        tenant_id="tenant-demo",
        name="Demo Tenant",
    )


@pytest.fixture
def authority() -> Authority:
    return Authority(
        actor_id="human:tshepo",
        level="human",
        can_execute=True,
        requires_approval=True,
    )


@pytest.fixture
def permissions() -> tuple[CapabilityPermission, ...]:
    return (
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="operations",
        ),
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="reporting",
        ),
    )


def test_active_tenant_is_authorized(
    planner: WorkforcePlanner,
    tenant: Tenant,
    authority: Authority,
    permissions: tuple[CapabilityPermission, ...],
) -> None:
    workforce = planner.plan(
        "WO-AUTH-001",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-001",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is True
    assert decision.execution_id == "exec:WO-AUTH-001"
    assert decision.actor_id == "human:tshepo"
    assert decision.tenant_id == "tenant-demo"


def test_inactive_tenant_is_denied(
    planner: WorkforcePlanner,
    authority: Authority,
    permissions: tuple[CapabilityPermission, ...],
) -> None:
    tenant = Tenant(
        tenant_id="tenant-demo",
        name="Demo Tenant",
        active=False,
    )

    workforce = planner.plan(
        "WO-AUTH-002",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-002",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is False
    assert "tenant is inactive" in decision.reasons


def test_tenant_mismatch_is_denied(
    planner: WorkforcePlanner,
    authority: Authority,
) -> None:
    tenant = Tenant(
        tenant_id="tenant-other",
        name="Other Tenant",
    )

    permissions = (
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="operations",
        ),
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="reporting",
        ),
    )

    workforce = planner.plan(
        "WO-AUTH-003",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-003",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is False
    assert any(
        reason.startswith("missing permission:")
        for reason in decision.reasons
    )


def test_actor_mismatch_is_denied(
    planner: WorkforcePlanner,
    tenant: Tenant,
    permissions: tuple[CapabilityPermission, ...],
) -> None:
    authority = Authority(
        actor_id="human:other",
        level="human",
        can_execute=True,
        requires_approval=True,
    )

    workforce = planner.plan(
        "WO-AUTH-004",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-004",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is False
    assert any(
        reason.startswith("missing permission:")
        for reason in decision.reasons
    )


def test_missing_capability_permission_is_denied(
    planner: WorkforcePlanner,
    tenant: Tenant,
    authority: Authority,
) -> None:
    permissions = (
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="operations",
        ),
    )

    workforce = planner.plan(
        "WO-AUTH-005",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-005",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is False
    assert "missing permission: reporting" in decision.reasons


def test_explicit_permission_denial_is_denied(
    planner: WorkforcePlanner,
    tenant: Tenant,
    authority: Authority,
) -> None:
    permissions = (
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="operations",
            allowed=True,
        ),
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="reporting",
            allowed=False,
        ),
    )

    workforce = planner.plan(
        "WO-AUTH-006",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-006",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is False
    assert "permission denied: reporting" in decision.reasons


def test_partial_capability_authorization_is_denied(
    planner: WorkforcePlanner,
    tenant: Tenant,
    authority: Authority,
) -> None:
    permissions = (
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="operations",
        ),
    )

    workforce = planner.plan(
        "WO-AUTH-007",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-007",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is False


def test_all_capabilities_authorized_succeeds(
    planner: WorkforcePlanner,
    tenant: Tenant,
    authority: Authority,
) -> None:
    permissions = (
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="operations",
        ),
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id="reporting",
        ),
    )

    workforce = planner.plan(
        "WO-AUTH-008",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-008",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is True


def test_authority_without_execution_permission_is_denied(
    planner: WorkforcePlanner,
    tenant: Tenant,
    permissions: tuple[CapabilityPermission, ...],
) -> None:
    authority = Authority(
        actor_id="human:tshepo",
        level="human",
        can_execute=False,
        requires_approval=True,
    )

    workforce = planner.plan(
        "WO-AUTH-009",
        "business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="exec:WO-AUTH-009",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=permissions,
    )

    assert decision.allowed is False
    assert "authority does not permit execution" in decision.reasons


@pytest.mark.parametrize(
    "execution_id",
    ["", "   "],
)
def test_empty_execution_identity_is_rejected(
    planner: WorkforcePlanner,
    tenant: Tenant,
    authority: Authority,
    permissions: tuple[CapabilityPermission, ...],
    execution_id: str,
) -> None:
    workforce = planner.plan(
        "WO-AUTH-010",
        "business operations report",
    )

    with pytest.raises(ValueError, match="execution_id is required"):
        AuthorizationEngine().evaluate(
            execution_id=execution_id,
            authority=authority,
            tenant=tenant,
            workforce=workforce,
            permissions=permissions,
        )


def test_empty_permission_identity_is_rejected() -> None:
    with pytest.raises(ValueError, match="actor_id is required"):
        CapabilityPermission(
            actor_id=" ",
            tenant_id="tenant-demo",
            capability_id="reporting",
        )

    with pytest.raises(ValueError, match="tenant_id is required"):
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id=" ",
            capability_id="reporting",
        )

    with pytest.raises(ValueError, match="capability_id is required"):
        CapabilityPermission(
            actor_id="human:tshepo",
            tenant_id="tenant-demo",
            capability_id=" ",
        )
