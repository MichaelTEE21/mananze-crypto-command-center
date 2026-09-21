"""Mananze OS dynamic workforce planner foundation."""

from dataclasses import dataclass

from mananze_os.skill_registry import SkillRegistry, default_skill_registry

from mananze_os.capability_registry import (
    Capability,
    CapabilityRegistry,
    default_capability_registry,
)


@dataclass(frozen=True)
class PlannedRole:
    role_id: str
    name: str
    objective: str
    capability_id: str
    skill_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DynamicWorkforcePlan:
    work_order_id: str
    objective: str
    roles: tuple[PlannedRole, ...]


class WorkforcePlanner:
    """Select a controlled workforce from the capability registry."""

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
        skill_registry: SkillRegistry | None = None,
    ) -> None:
        self.registry = registry or default_capability_registry()
        self.skill_registry = skill_registry or default_skill_registry()

    def plan(
        self,
        work_order_id: str,
        objective: str,
    ) -> DynamicWorkforcePlan:
        if not work_order_id.strip():
            raise ValueError("work_order_id is required")

        if not objective.strip():
            raise ValueError("objective is required")

        objective_text = objective.lower()

        capability_ids: list[str] = []

        if any(
            word in objective_text
            for word in ("patient", "booking", "appointment", "customer")
        ):
            capability_ids.extend(
                [
                    "marketing",
                    "lead_generation",
                    "sales",
                    "appointment_booking",
                    "customer_communications",
                    "retention",
                    "revenue",
                    "reporting",
                ]
            )

        elif any(
            word in objective_text
            for word in ("delivery", "logistics", "fleet", "transport")
        ):
            capability_ids.extend(
                [
                    "operations",
                    "logistics",
                    "fleet",
                    "cost_analysis",
                    "revenue",
                    "reporting",
                ]
            )

        else:
            capability_ids.extend(
                [
                    "operations",
                    "reporting",
                ]
            )

        roles: list[PlannedRole] = []

        for capability_id in capability_ids:
            capability: Capability = self.registry.get(capability_id)

            required_skill_ids = {
                "marketing": (
                    "marketing:campaign_planning",
                    "marketing:content_creation",
                ),
                "lead_generation": (
                    "lead_generation:prospecting",
                    "lead_generation:qualification",
                ),
                "sales": (
                    "sales:lead_qualification",
                    "sales:follow_up",
                ),
                "appointment_booking": (
                    "appointment_booking:scheduling",
                ),
                "customer_communications": (
                    "customer_communications:messaging",
                ),
                "retention": (
                    "retention:engagement",
                ),
                "revenue": (
                    "revenue:performance_analysis",
                ),
                "operations": (
                    "operations:workflow_coordination",
                ),
                "logistics": (
                    "logistics:route_planning",
                ),
                "fleet": (
                    "fleet:fleet_monitoring",
                ),
                "cost_analysis": (
                    "cost_analysis:cost_review",
                ),
                "reporting": (
                    "reporting:business_reporting",
                ),
            }.get(capability.capability_id, ())

            for skill_id in required_skill_ids:
                self.skill_registry.get(skill_id)

            roles.append(
                PlannedRole(
                    role_id=capability.capability_id,
                    name=capability.name,
                    objective=capability.description,
                    capability_id=capability.capability_id,
                    skill_ids=required_skill_ids,
                )
            )

        return DynamicWorkforcePlan(
            work_order_id=work_order_id,
            objective=objective.strip(),
            roles=tuple(roles),
        )


__all__ = [
    "PlannedRole",
    "DynamicWorkforcePlan",
    "WorkforcePlanner",
]
