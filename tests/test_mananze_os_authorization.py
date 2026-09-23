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

from mananze_os.intelligence_fabric import IntelligenceFabric
from mananze_os.intelligence_provider import (
    IntelligenceCoordinator,
    IntelligenceProviderRegistry,
)
from mananze_os.obligation_intelligence_provider import ObligationIntelligenceProvider
from mananze_os.obligation_registry import ObligationRegistry
from mananze_os.obligation_intelligence import Obligation


def test_intelligence_observation_does_not_grant_execution_authority():
    obligation_registry = ObligationRegistry()
    obligation_registry.register(
        Obligation(
            obligation_id="obligation-auth-1",
            tenant_id="tenant-demo",
            name="Monthly supplier payment",
            obligation_type="payment",
            counterparty="Supplier",
            amount=1000.0,
            currency="ZAR",
            frequency="monthly",
            due_date=None,
            renewal_date=None,
            status="active",
            approval_required=True,
            source_reference="source-1",
        )
    )

    provider = ObligationIntelligenceProvider(obligation_registry)
    fabric = IntelligenceFabric()
    registry = IntelligenceProviderRegistry()
    registry.register(provider)
    coordinator = IntelligenceCoordinator(fabric, registry)

    observations = coordinator.collect(
        provider_id="mananze:obligations",
        tenant_id="tenant-demo",
    )

    assert len(observations) == 1
    assert observations[0].domain == "obligations"

    authority = Authority(
        actor_id="agent:obligations",
        level="agent",
        can_execute=False,
        requires_approval=True,
    )

    tenant = Tenant(tenant_id="tenant-demo", name="Demo Tenant")
    planner = WorkforcePlanner()
    workforce = planner.plan(
        work_order_id="wo-intelligence-auth-1",
        objective="business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="execution-intelligence-1",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=(),
    )

    assert decision.allowed is False
    assert "authority does not permit execution" in decision.reasons


def test_intelligence_does_not_create_permissions():
    obligation_registry = ObligationRegistry()
    obligation_registry.register(
        Obligation(
            obligation_id="obligation-auth-2",
            tenant_id="tenant-demo",
            name="Monthly software subscription",
            obligation_type="subscription",
            counterparty="Software Vendor",
            amount=500.0,
            currency="ZAR",
            frequency="monthly",
            due_date=None,
            renewal_date=None,
            status="active",
            approval_required=True,
            source_reference="source-2",
        )
    )

    provider = ObligationIntelligenceProvider(obligation_registry)
    observations = provider.observe(tenant_id="tenant-demo")

    assert len(observations) == 1

    value = observations[0].value

    assert "actor_id" not in value
    assert "capability_id" not in value
    assert "allowed" not in value
    assert observations[0].tenant_id == "tenant-demo"


def test_intelligence_cannot_bypass_missing_permission():
    obligation_registry = ObligationRegistry()
    obligation_registry.register(
        Obligation(
            obligation_id="obligation-auth-3",
            tenant_id="tenant-demo",
            name="Fleet service obligation",
            obligation_type="maintenance",
            counterparty="Workshop",
            amount=2000.0,
            currency="ZAR",
            frequency="monthly",
            due_date=None,
            renewal_date=None,
            status="active",
            approval_required=True,
            source_reference="source-3",
        )
    )

    provider = ObligationIntelligenceProvider(obligation_registry)
    observations = provider.observe(tenant_id="tenant-demo")

    assert observations

    authority = Authority(
        actor_id="human:tshepo",
        level="human",
        can_execute=True,
        requires_approval=True,
    )

    tenant = Tenant(tenant_id="tenant-demo", name="Demo Tenant")
    planner = WorkforcePlanner()
    workforce = planner.plan(
        work_order_id="wo-intelligence-auth-3",
        objective="business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="execution-intelligence-2",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=(),
    )

    assert decision.allowed is False
    assert any(
        "missing permission" in reason
        for reason in decision.reasons
    )


def test_intelligence_provider_cannot_change_authorization_state():
    obligation_registry = ObligationRegistry()
    obligation_registry.register(
        Obligation(
            obligation_id="obligation-auth-4",
            tenant_id="tenant-demo",
            name="Vehicle insurance renewal",
            obligation_type="insurance",
            counterparty="Insurer",
            amount=1500.0,
            currency="ZAR",
            frequency="annual",
            due_date=None,
            renewal_date=None,
            status="active",
            approval_required=True,
            source_reference="source-4",
        )
    )

    provider = ObligationIntelligenceProvider(obligation_registry)
    observations = provider.observe(tenant_id="tenant-demo")

    authority = Authority(
        actor_id="agent:obligations",
        level="agent",
        can_execute=False,
        requires_approval=True,
    )

    tenant = Tenant(tenant_id="tenant-demo", name="Demo Tenant")
    planner = WorkforcePlanner()
    workforce = planner.plan(
        work_order_id="wo-intelligence-auth-4",
        objective="business operations report",
    )

    decision = AuthorizationEngine().evaluate(
        execution_id="execution-intelligence-3",
        authority=authority,
        tenant=tenant,
        workforce=workforce,
        permissions=(),
    )

    assert decision.allowed is False
    assert observations[0].domain == "obligations"
    assert observations[0].kind == "fact"
    assert observations[0].tenant_id == "tenant-demo"

from mananze_os.approval_gate import ApprovalGate
from mananze_os.domain_qa import DomainQA
from mananze_os.intelligence_fabric import IntelligenceObservation
from mananze_os.policy_engine import PolicyEngine
from mananze_os.policy import Policy
from mananze_os.workforce_planner import WorkforcePlanner


def test_intelligence_cannot_change_policy_decision():
    planner = WorkforcePlanner()
    workforce = planner.plan(
        work_order_id="wo-intelligence-policy-1",
        objective="business operations report",
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:policy:001",
        tenant_id="tenant-demo",
        domain="business",
        kind="recommendation",
        subject="recommended_policy_effect",
        value={"effect": "allow", "autonomy_level": 4},
        confidence=1.0,
        source_reference="intelligence:test",
    )

    policy = Policy(
        policy_id="policy-deny-operations",
        name="Deny operations",
        effect="deny",
        description="Operations are denied for this test.",
        capability_ids=("operations",),
    )

    decision = PolicyEngine().evaluate(
        workforce=workforce,
        policies=(policy,),
    )

    assert intelligence.value["effect"] == "allow"
    assert intelligence.value["autonomy_level"] == 4
    assert decision.effect == "deny"
    assert decision.autonomy_level == 0


def test_intelligence_cannot_elevate_policy_autonomy():
    planner = WorkforcePlanner()
    workforce = planner.plan(
        work_order_id="wo-intelligence-policy-2",
        objective="business operations report",
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:policy:002",
        tenant_id="tenant-demo",
        domain="business",
        kind="recommendation",
        subject="recommended_autonomy",
        value={"autonomy_level": 4},
        confidence=1.0,
        source_reference="intelligence:test",
    )

    decision = PolicyEngine().evaluate(workforce=workforce)

    assert intelligence.value["autonomy_level"] == 4
    assert decision.autonomy_level == 3


def test_intelligence_cannot_approve_execution():
    planner = WorkforcePlanner()
    workforce = planner.plan(
        work_order_id="wo-intelligence-approval-1",
        objective="business operations report",
    )

    qa_verdict = DomainQA().verify(workforce)
    approval = ApprovalGate().request(
        execution_id="execution-intelligence-approval-1",
        qa_verdict=qa_verdict,
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:approval:001",
        tenant_id="tenant-demo",
        domain="business",
        kind="recommendation",
        subject="approval",
        value={
            "status": "approved",
            "decided_by": "agent:intelligence",
        },
        confidence=1.0,
        source_reference="intelligence:test",
    )

    assert intelligence.value["status"] == "approved"
    assert approval.status == "pending"
    assert approval.decided_by is None
