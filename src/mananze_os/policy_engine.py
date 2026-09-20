"""Mananze OS policy evaluation engine."""

from mananze_os.policy import Policy
from mananze_os.policy_decision import PolicyDecision
from mananze_os.risk import RiskLevel
from mananze_os.workforce_planner import DynamicWorkforcePlan


class PolicyEngine:
    """Evaluate whether a planned workforce may proceed."""

    _RISK_BY_CAPABILITY: dict[str, RiskLevel] = {
        "marketing": "low",
        "lead_generation": "low",
        "reporting": "low",
        "cost_analysis": "medium",
        "operations": "medium",
        "logistics": "medium",
        "fleet": "high",
        "appointment_booking": "medium",
        "customer_communications": "high",
        "retention": "medium",
        "sales": "high",
        "revenue": "high",
    }

    def evaluate(
        self,
        workforce: DynamicWorkforcePlan,
        policies: tuple[Policy, ...] = (),
    ) -> PolicyDecision:
        if not workforce.work_order_id.strip():
            raise ValueError("work_order_id is required")

        capability_ids = tuple(
            role.capability_id
            for role in workforce.roles
        )

        if not capability_ids:
            return PolicyDecision(
                work_order_id=workforce.work_order_id,
                effect="deny",
                risk="critical",
                autonomy_level=0,
                reasons=("no capabilities available for policy evaluation",),
            )

        unknown = tuple(
            capability_id
            for capability_id in capability_ids
            if capability_id not in self._RISK_BY_CAPABILITY
        )

        if unknown:
            reasons = tuple(
                f"unsupported capability: {capability_id}"
                for capability_id in unknown
            )

            return PolicyDecision(
                work_order_id=workforce.work_order_id,
                effect="deny",
                risk="critical",
                autonomy_level=0,
                reasons=reasons,
            )

        risks = [
            self._RISK_BY_CAPABILITY[capability_id]
            for capability_id in capability_ids
        ]

        if "critical" in risks:
            highest_risk: RiskLevel = "critical"
        elif "high" in risks:
            highest_risk = "high"
        elif "medium" in risks:
            highest_risk = "medium"
        else:
            highest_risk = "low"

        policy_effects = {
            policy.effect
            for policy in policies
            if not policy.capability_ids
            or any(
                capability_id in policy.capability_ids
                for capability_id in capability_ids
            )
        }

        if "deny" in policy_effects:
            return PolicyDecision(
                work_order_id=workforce.work_order_id,
                effect="deny",
                risk=highest_risk,
                autonomy_level=0,
                reasons=("explicit deny policy matched",),
            )

        if "approval_required" in policy_effects or highest_risk in {
            "high",
            "critical",
        }:
            return PolicyDecision(
                work_order_id=workforce.work_order_id,
                effect="approval_required",
                risk=highest_risk,
                autonomy_level=2,
                reasons=(
                    "human approval required for elevated-risk capabilities",
                ),
            )

        return PolicyDecision(
            work_order_id=workforce.work_order_id,
            effect="allow",
            risk=highest_risk,
            autonomy_level=3,
            reasons=(
                "capabilities passed policy evaluation",
                "no elevated-risk capability detected",
            ),
        )


__all__ = ["PolicyEngine"]
