"""Mananze OS execution authorization engine."""

from dataclasses import dataclass

from mananze_os.authority import Authority
from mananze_os.permission import CapabilityPermission
from mananze_os.tenant import Tenant
from mananze_os.workforce_planner import DynamicWorkforcePlan


@dataclass(frozen=True)
class AuthorizationDecision:
    execution_id: str
    actor_id: str
    tenant_id: str
    allowed: bool
    reasons: tuple[str, ...]


class AuthorizationEngine:
    """Authorize a specific execution within a tenant boundary."""

    def evaluate(
        self,
        execution_id: str,
        authority: Authority,
        tenant: Tenant,
        workforce: DynamicWorkforcePlan,
        permissions: tuple[CapabilityPermission, ...],
    ) -> AuthorizationDecision:
        reasons: list[str] = []

        if not execution_id.strip():
            raise ValueError("execution_id is required")

        actor_id = authority.actor_id

        if not actor_id.strip():
            raise ValueError("actor_id is required")

        if not tenant.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not authority.can_execute:
            reasons.append("authority does not permit execution")

        if not tenant.active:
            reasons.append("tenant is inactive")

        if not workforce.work_order_id.strip():
            reasons.append("work order identity is missing")

        required_capabilities = tuple(
            role.capability_id
            for role in workforce.roles
        )

        if not required_capabilities:
            reasons.append("no required capabilities")

        if any(
            not capability_id.strip()
            for capability_id in required_capabilities
        ):
            reasons.append("workforce contains an empty capability ID")

        if len(required_capabilities) != len(set(required_capabilities)):
            reasons.append("duplicate capability detected")

        for capability_id in required_capabilities:
            matching = tuple(
                permission
                for permission in permissions
                if permission.actor_id == actor_id
                and permission.tenant_id == tenant.tenant_id
                and permission.capability_id == capability_id
            )

            if not matching:
                reasons.append(
                    f"missing permission: {capability_id}"
                )
                continue

            if not any(permission.allowed for permission in matching):
                reasons.append(
                    f"permission denied: {capability_id}"
                )

        if reasons:
            return AuthorizationDecision(
                execution_id=execution_id,
                actor_id=actor_id,
                tenant_id=tenant.tenant_id,
                allowed=False,
                reasons=tuple(reasons),
            )

        return AuthorizationDecision(
            execution_id=execution_id,
            actor_id=actor_id,
            tenant_id=tenant.tenant_id,
            allowed=True,
            reasons=(
                "authority permits execution",
                "tenant is active",
                "actor identity is bound to authority",
                "all required capabilities are authorized",
                "authorization is bound to execution identity",
            ),
        )


__all__ = [
    "AuthorizationDecision",
    "AuthorizationEngine",
]
