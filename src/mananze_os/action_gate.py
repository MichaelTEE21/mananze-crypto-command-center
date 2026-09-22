"""Mananze OS central action authorization boundary."""

from dataclasses import dataclass
from typing import Literal


ActionGateEffect = Literal[
    "allow",
    "deny",
    "approval_required",
]


@dataclass(frozen=True)
class ActionRequest:
    """A structured action proposed for execution."""

    action_id: str
    tenant_id: str
    execution_id: str
    task_id: str
    actor_id: str
    tool_id: str
    capability_id: str
    action: str
    risk: str
    payload: object
    requires_approval: bool = False

    def __post_init__(self) -> None:
        required_fields = {
            "action_id": self.action_id,
            "tenant_id": self.tenant_id,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "actor_id": self.actor_id,
            "tool_id": self.tool_id,
            "capability_id": self.capability_id,
            "action": self.action,
            "risk": self.risk,
        }

        for field_name, value in required_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")


@dataclass(frozen=True)
class ActionGateDecision:
    """Decision returned by the central Action Gate."""

    action_id: str
    execution_id: str
    tenant_id: str
    effect: ActionGateEffect
    reasons: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.effect == "allow"


class ActionGate:
    """Central boundary for proposed consequential actions.

    The Action Gate evaluates an action proposal. It does not allow
    agents to manufacture permissions, bypass policy, or approve
    their own actions.
    """

    def evaluate(
        self,
        request: ActionRequest,
        *,
        tenant_allowed: bool,
        permission_allowed: bool,
        policy_effect: str,
        economic_allowed: bool = True,
    ) -> ActionGateDecision:
        reasons: list[str] = []

        if not tenant_allowed:
            reasons.append("tenant access denied")

        if not permission_allowed:
            reasons.append("permission denied")

        if policy_effect == "deny":
            reasons.append("policy denied")

        if not economic_allowed:
            reasons.append("economic/resource constraint exceeded")

        if reasons:
            return ActionGateDecision(
                action_id=request.action_id,
                execution_id=request.execution_id,
                tenant_id=request.tenant_id,
                effect="deny",
                reasons=tuple(reasons),
            )

        if request.requires_approval or policy_effect == "approval_required":
            return ActionGateDecision(
                action_id=request.action_id,
                execution_id=request.execution_id,
                tenant_id=request.tenant_id,
                effect="approval_required",
                reasons=("human approval required",),
            )

        return ActionGateDecision(
            action_id=request.action_id,
            execution_id=request.execution_id,
            tenant_id=request.tenant_id,
            effect="allow",
            reasons=("action passed gate checks",),
        )


__all__ = [
    "ActionGate",
    "ActionGateDecision",
    "ActionGateEffect",
    "ActionRequest",
]
