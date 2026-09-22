"""Mananze OS dynamic workforce planner foundation."""

from dataclasses import dataclass

from mananze_os.compiler import (
    CompiledRequirement,
    IntelligenceCompiler,
)
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
    """Select a controlled workforce from compiled capability requirements."""

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
        skill_registry: SkillRegistry | None = None,
        compiler: IntelligenceCompiler | None = None,
    ) -> None:
        self.registry = registry or default_capability_registry()
        self.skill_registry = skill_registry or default_skill_registry()
        self.compiler = compiler or IntelligenceCompiler(self.registry)

    def plan_from_requirements(
        self,
        work_order_id: str,
        objective: str,
        requirements: tuple[CompiledRequirement, ...],
    ) -> DynamicWorkforcePlan:
        if not work_order_id.strip():
            raise ValueError("work_order_id is required")

        if not objective.strip():
            raise ValueError("objective is required")

        roles: list[PlannedRole] = []

        for requirement in requirements:
            capability: Capability = self.registry.get(
                requirement.capability_id
            )

            required_skill_ids = tuple(
                skill.skill_id
                for skill in self.skill_registry.list_for_capability(
                    capability.capability_id
                )
            )

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

    def plan(
        self,
        work_order_id: str,
        objective: str,
    ) -> DynamicWorkforcePlan:
        if not work_order_id.strip():
            raise ValueError("work_order_id is required")

        if not objective.strip():
            raise ValueError("objective is required")

        from mananze_os.work_order import WorkOrder

        work_order = WorkOrder(
            work_order_id=work_order_id,
            tenant_id="planner-compatibility",
            objective=objective.strip(),
        )

        compiled = self.compiler.compile(work_order)

        return self.plan_from_requirements(
            work_order_id=compiled.work_order_id,
            objective=compiled.objective,
            requirements=compiled.requirements,
        )


__all__ = [
    "PlannedRole",
    "DynamicWorkforcePlan",
    "WorkforcePlanner",
]
