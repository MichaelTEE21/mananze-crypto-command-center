"""Governed bridge from activated capabilities to the canonical workforce."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.capability_activation import CapabilityActivationPlan
from mananze_os.compiler import CompiledRequirement
from mananze_os.execution_graph import ExecutionGraph, ExecutionNode
from mananze_os.work_order import WorkOrder
from mananze_os.workforce_fabric import WorkforceFabric
from mananze_os.workforce_planner import (
    DynamicWorkforcePlan,
    WorkforcePlanner,
)


@dataclass(frozen=True)
class WorkforceSelection:
    """A governed selection of canonical workforce roles."""

    tenant_id: str
    twin_id: str
    work_order_id: str
    capability_id: str
    role_ids: tuple[str, ...]
    skill_ids: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityWorkforcePlan:
    """Workforce plan derived from an activated capability plan."""

    tenant_id: str
    twin_id: str
    work_order_id: str
    objective: str
    selections: tuple[WorkforceSelection, ...]
    dynamic_plan: DynamicWorkforcePlan
    execution_graph: ExecutionGraph


class CapabilityWorkforceBridge:
    """
    Convert activated capability requirements into selections from the
    canonical Mananze workforce.

    This bridge does not grant authority, execute actions, bypass Policy,
    Authorization, Approval, or create new workforce roles.
    """

    def __init__(
        self,
        workforce_fabric: WorkforceFabric | None = None,
        workforce_planner: WorkforcePlanner | None = None,
    ) -> None:
        self.workforce_fabric = (
            workforce_fabric
            or WorkforceFabric.with_default_workforce()
        )
        self.workforce_planner = (
            workforce_planner
            or WorkforcePlanner()
        )

    @staticmethod
    def _role_matches_requirement(
        role,
        capability_id: str,
        required_skill_ids: tuple[str, ...],
    ) -> bool:
        if capability_id not in role.capability_ids:
            return False

        return set(required_skill_ids).issubset(
            set(role.skill_ids)
        )

    def _select_roles(
        self,
        requirement: CompiledRequirement,
        planned_role,
    ) -> tuple:
        required_skill_ids = planned_role.skill_ids

        matches = tuple(
            role
            for role in self.workforce_fabric.list_roles()
            if self._role_matches_requirement(
                role,
                requirement.capability_id,
                required_skill_ids,
            )
        )

        if not matches:
            raise LookupError(
                "no canonical workforce role satisfies capability "
                f"{requirement.capability_id} and required skills "
                f"{required_skill_ids}"
            )

        orchestrators = tuple(
            role
            for role in matches
            if role.role_id.startswith("orchestrator:")
        )

        specialists = tuple(
            role
            for role in matches
            if not role.role_id.startswith("orchestrator:")
        )

        selected = []

        if orchestrators:
            selected.append(orchestrators[0])

        if specialists:
            selected.append(specialists[0])

        return tuple(selected)

    def build(
        self,
        activation_plan: CapabilityActivationPlan,
        work_order_id: str,
        objective: str,
    ) -> CapabilityWorkforcePlan:
        if not activation_plan.tenant_id.strip():
            raise ValueError("activation tenant_id is required")

        if not activation_plan.twin_id.strip():
            raise ValueError("activation twin_id is required")

        if not work_order_id.strip():
            raise ValueError("work_order_id is required")

        if not objective.strip():
            raise ValueError("objective is required")

        if not activation_plan.active_capability_ids:
            raise ValueError(
                "cannot build workforce plan without active capabilities"
            )

        work_order = WorkOrder(
            work_order_id=work_order_id,
            tenant_id=activation_plan.tenant_id,
            objective=objective.strip(),
        )

        compiled = self.workforce_planner.compiler.compile(
            work_order,
            candidate_capability_ids=(
                activation_plan.active_capability_ids
            ),
        )

        dynamic_plan = self.workforce_planner.plan_from_requirements(
            work_order_id=compiled.work_order_id,
            objective=compiled.objective,
            requirements=compiled.requirements,
        )

        if len(compiled.requirements) != len(dynamic_plan.roles):
            raise RuntimeError(
                "compiled requirements and dynamic workforce roles "
                "are misaligned"
            )

        selections: list[WorkforceSelection] = []
        nodes: list[ExecutionNode] = []

        for requirement, planned_role in zip(
            compiled.requirements,
            dynamic_plan.roles,
        ):
            roles = self._select_roles(
                requirement,
                planned_role,
            )

            role_ids = tuple(
                role.role_id
                for role in roles
            )

            selections.append(
                WorkforceSelection(
                    tenant_id=activation_plan.tenant_id,
                    twin_id=activation_plan.twin_id,
                    work_order_id=work_order_id,
                    capability_id=requirement.capability_id,
                    role_ids=role_ids,
                    skill_ids=tuple(planned_role.skill_ids),
                )
            )

            nodes.append(
                ExecutionNode(
                    node_id=(
                        f"{work_order_id}:"
                        f"{requirement.capability_id}"
                    ),
                    capability_id=requirement.capability_id,
                    skill_ids=tuple(planned_role.skill_ids),
                )
            )

        graph = ExecutionGraph(
            graph_id=f"{work_order_id}:workforce",
            nodes=tuple(nodes),
        )

        return CapabilityWorkforcePlan(
            tenant_id=activation_plan.tenant_id,
            twin_id=activation_plan.twin_id,
            work_order_id=work_order_id,
            objective=objective.strip(),
            selections=tuple(selections),
            dynamic_plan=dynamic_plan,
            execution_graph=graph,
        )


__all__ = [
    "WorkforceSelection",
    "CapabilityWorkforcePlan",
    "CapabilityWorkforceBridge",
]
