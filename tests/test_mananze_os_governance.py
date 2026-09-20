"""Tests for Mananze OS governance and policy controls."""

import pytest

from mananze_os.capability_registry import default_capability_registry
from mananze_os.policy import Policy
from mananze_os.policy_engine import PolicyEngine
from mananze_os.workforce_planner import WorkforcePlanner


@pytest.fixture
def planner() -> WorkforcePlanner:
    return WorkforcePlanner(default_capability_registry())


@pytest.fixture
def engine() -> PolicyEngine:
    return PolicyEngine()


def test_low_risk_workforce_is_allowed(
    planner: WorkforcePlanner,
    engine: PolicyEngine,
) -> None:
    workforce = planner.plan(
        "wo-governance-low",
        "produce a business report",
    )

    decision = engine.evaluate(workforce)

    assert decision.effect == "allow"
    assert decision.risk == "medium"
    assert decision.autonomy_level == 3
    assert decision.work_order_id == "wo-governance-low"


def test_high_risk_workforce_requires_approval(
    planner: WorkforcePlanner,
    engine: PolicyEngine,
) -> None:
    workforce = planner.plan(
        "wo-governance-high",
        "manage customer communications",
    )

    decision = engine.evaluate(workforce)

    assert decision.effect == "approval_required"
    assert decision.risk == "high"
    assert decision.autonomy_level == 2
    assert "human approval" in decision.reasons[0]


def test_unknown_capability_is_denied(
    planner: WorkforcePlanner,
    engine: PolicyEngine,
) -> None:
    workforce = planner.plan(
        "wo-governance-unknown",
        "produce a business report",
    )

    unknown_role = workforce.roles[0]

    from mananze_os.workforce_planner import (
        DynamicWorkforcePlan,
        PlannedRole,
    )

    modified = DynamicWorkforcePlan(
        work_order_id=workforce.work_order_id,
        objective=workforce.objective,
        roles=(
            PlannedRole(
                role_id=unknown_role.role_id,
                name=unknown_role.name,
                objective=unknown_role.objective,
                capability_id="unknown_capability",
            ),
        ),
    )

    decision = engine.evaluate(modified)

    assert decision.effect == "deny"
    assert decision.risk == "critical"
    assert decision.autonomy_level == 0
    assert "unsupported capability" in decision.reasons[0]


def test_explicit_deny_policy_overrides_normal_evaluation(
    planner: WorkforcePlanner,
    engine: PolicyEngine,
) -> None:
    workforce = planner.plan(
        "wo-governance-deny",
        "produce a business report",
    )

    policy = Policy(
        policy_id="policy:test-deny",
        name="Test Deny",
        effect="deny",
        description="Test policy denying reporting.",
        capability_ids=("reporting",),
    )

    decision = engine.evaluate(
        workforce,
        policies=(policy,),
    )

    assert decision.effect == "deny"
    assert decision.autonomy_level == 0
    assert "explicit deny policy matched" in decision.reasons


def test_empty_workforce_is_denied(
    planner: WorkforcePlanner,
    engine: PolicyEngine,
) -> None:
    from mananze_os.workforce_planner import DynamicWorkforcePlan

    workforce = DynamicWorkforcePlan(
        work_order_id="wo-governance-empty",
        objective="empty workforce test",
        roles=(),
    )

    decision = engine.evaluate(workforce)

    assert decision.effect == "deny"
    assert decision.risk == "critical"
    assert decision.autonomy_level == 0


def test_missing_work_order_id_is_rejected(
    planner: WorkforcePlanner,
    engine: PolicyEngine,
) -> None:
    workforce = planner.plan(
        "wo-governance-invalid",
        "produce a business report",
    )

    from mananze_os.workforce_planner import DynamicWorkforcePlan

    invalid = DynamicWorkforcePlan(
        work_order_id="",
        objective=workforce.objective,
        roles=workforce.roles,
    )

    with pytest.raises(ValueError, match="work_order_id is required"):
        engine.evaluate(invalid)
