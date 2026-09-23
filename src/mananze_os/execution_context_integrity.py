"""Mananze OS execution-context integrity contract."""

from dataclasses import dataclass

from mananze_os.compiler import CompiledPlan
from mananze_os.workforce_planner import DynamicWorkforcePlan
from mananze_os.work_order import WorkOrder


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable binding of the existing execution artifacts."""

    work_order_id: str
    tenant_id: str
    execution_id: str
    task_id: str


class ExecutionContextIntegrity:
    """Validate that execution artifacts belong to one governed context."""

    def bind(
        self,
        work_order: WorkOrder,
        plan: CompiledPlan,
        workforce: DynamicWorkforcePlan,
        execution_id: str,
        task_id: str,
    ) -> ExecutionContext:
        self._require_match(
            "work_order_id",
            work_order.work_order_id,
            plan.work_order_id,
        )
        self._require_match(
            "work_order_id",
            work_order.work_order_id,
            workforce.work_order_id,
        )
        self._require_match(
            "objective",
            work_order.objective.strip(),
            plan.objective.strip(),
        )
        self._require_match(
            "objective",
            plan.objective.strip(),
            workforce.objective.strip(),
        )

        if not execution_id.strip():
            raise ValueError("execution_id is required")

        if not task_id.strip():
            raise ValueError("task_id is required")

        expected_execution_id = f"exec:{work_order.work_order_id}"
        expected_task_id = f"task:{work_order.work_order_id}"

        if execution_id != expected_execution_id:
            raise ValueError(
                "execution_id does not belong to work_order"
            )

        if task_id != expected_task_id:
            raise ValueError(
                "task_id does not belong to work_order"
            )

        requirement_ids = {
            requirement.capability_id
            for requirement in plan.requirements
        }

        workforce_capability_ids = {
            role.capability_id
            for role in workforce.roles
        }

        missing_capabilities = requirement_ids - workforce_capability_ids

        if missing_capabilities:
            raise ValueError(
                "workforce is missing compiled capabilities: "
                + ", ".join(sorted(missing_capabilities))
            )

        unexpected_capabilities = (
            workforce_capability_ids - requirement_ids
        )

        if unexpected_capabilities:
            raise ValueError(
                "workforce contains uncompiled capabilities: "
                + ", ".join(sorted(unexpected_capabilities))
            )

        if plan.tenant_id != work_order.tenant_id:
            raise PermissionError(
                "compiled plan tenant does not match work order tenant"
            )

        return ExecutionContext(
            work_order_id=work_order.work_order_id,
            tenant_id=work_order.tenant_id,
            execution_id=execution_id,
            task_id=task_id,
        )

    @staticmethod
    def _require_match(
        field: str,
        expected: str,
        actual: str,
    ) -> None:
        if expected != actual:
            raise ValueError(
                f"{field} does not match execution context"
            )


__all__ = [
    "ExecutionContext",
    "ExecutionContextIntegrity",
]
