"""Mananze OS intelligence compiler foundation."""

from dataclasses import dataclass

from mananze_os.work_order import WorkOrder


@dataclass(frozen=True)
class CompiledPlan:
    work_order_id: str
    tenant_id: str
    objective: str
    domain: str
    stages: tuple[str, ...]


class IntelligenceCompiler:
    """Convert an accepted work order into a controlled execution plan."""

    def compile(self, work_order: WorkOrder) -> CompiledPlan:
        if not work_order.work_order_id.strip():
            raise ValueError("work_order_id is required")

        if not work_order.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not work_order.objective.strip():
            raise ValueError("objective is required")

        return CompiledPlan(
            work_order_id=work_order.work_order_id,
            tenant_id=work_order.tenant_id,
            objective=work_order.objective.strip(),
            domain="business",
            stages=(
                "understand",
                "plan",
                "execute",
                "verify",
                "report",
            ),
        )


__all__ = ["CompiledPlan", "IntelligenceCompiler"]
