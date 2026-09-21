"""Mananze OS intelligence compiler foundation."""

from dataclasses import dataclass

from mananze_os.capability_registry import CapabilityRegistry, default_capability_registry
from mananze_os.work_order import WorkOrder


@dataclass(frozen=True)
class CompiledRequirement:
    capability_id: str

    def __post_init__(self) -> None:
        if not self.capability_id.strip():
            raise ValueError("capability_id is required")


@dataclass(frozen=True)
class CompiledPlan:
    work_order_id: str
    tenant_id: str
    objective: str
    domain: str
    stages: tuple[str, ...]
    requirements: tuple[CompiledRequirement, ...] = ()


class IntelligenceCompiler:
    """Convert an accepted work order into a controlled execution plan."""

    def __init__(
        self,
        capability_registry: CapabilityRegistry | None = None,
    ) -> None:
        self.capability_registry = (
            capability_registry or default_capability_registry()
        )

    def _compile_requirements(
        self,
        objective: str,
    ) -> tuple[CompiledRequirement, ...]:
        objective_text = objective.lower()

        if any(
            word in objective_text
            for word in ("patient", "booking", "appointment", "customer")
        ):
            capability_ids = (
                "marketing",
                "lead_generation",
                "sales",
                "appointment_booking",
                "customer_communications",
                "retention",
                "revenue",
                "reporting",
            )
        elif any(
            word in objective_text
            for word in ("delivery", "logistics", "fleet", "transport")
        ):
            capability_ids = (
                "operations",
                "logistics",
                "fleet",
                "cost_analysis",
                "revenue",
                "reporting",
            )
        else:
            capability_ids = (
                "operations",
                "reporting",
            )

        requirements = []

        for capability_id in capability_ids:
            self.capability_registry.get(capability_id)
            requirements.append(
                CompiledRequirement(capability_id=capability_id)
            )

        return tuple(requirements)

    def compile(self, work_order: WorkOrder) -> CompiledPlan:
        if not work_order.work_order_id.strip():
            raise ValueError("work_order_id is required")

        if not work_order.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not work_order.objective.strip():
            raise ValueError("objective is required")

        objective = work_order.objective.strip()
        requirements = self._compile_requirements(objective)

        return CompiledPlan(
            work_order_id=work_order.work_order_id,
            tenant_id=work_order.tenant_id,
            objective=objective,
            domain="business",
            stages=(
                "understand",
                "plan",
                "execute",
                "verify",
                "report",
            ),
            requirements=requirements,
        )


__all__ = ["CompiledRequirement", "CompiledPlan", "IntelligenceCompiler"]
