"""Bridge accepted diagnostic scopes into the existing execution planning pipeline."""

from dataclasses import dataclass

from mananze_os.compiler import CompiledPlan, IntelligenceCompiler
from mananze_os.diagnostic import ImplementationScope
from mananze_os.input_gate import InputGate
from mananze_os.input_request import InputRequest
from mananze_os.workforce_planner import DynamicWorkforcePlan, WorkforcePlanner
from mananze_os.work_order import WorkOrder


@dataclass(frozen=True)
class ImplementationCompilation:
    """Controlled compilation result for an accepted implementation scope."""

    scope: ImplementationScope
    work_order: WorkOrder
    compiled_plan: CompiledPlan
    workforce_plan: DynamicWorkforcePlan


class DiagnosticImplementationBridge:
    """Convert an accepted diagnostic scope into an executable workforce plan.

    This bridge composes existing Mananze OS components. It does not grant
    execution authority, approve actions, or execute providers.
    """

    def __init__(
        self,
        *,
        input_gate: InputGate | None = None,
        compiler: IntelligenceCompiler | None = None,
        workforce_planner: WorkforcePlanner | None = None,
    ) -> None:
        self.input_gate = input_gate or InputGate()
        self.compiler = compiler or IntelligenceCompiler()
        self.workforce_planner = workforce_planner or WorkforcePlanner(
            compiler=self.compiler,
        )

    def compile_accepted_scope(
        self,
        *,
        scope: ImplementationScope,
        request: InputRequest,
    ) -> ImplementationCompilation:
        if scope.tenant_id.strip() == "":
            raise ValueError("scope tenant_id is required")

        if request.tenant_id.strip() == "":
            raise ValueError("request tenant_id is required")

        if scope.tenant_id != request.tenant_id:
            raise PermissionError(
                "scope tenant_id does not match request tenant_id"
            )

        if scope.objective.strip() == "":
            raise ValueError("scope objective is required")

        if request.objective.strip() == "":
            raise ValueError("request objective is required")

        if scope.objective.strip() != request.objective.strip():
            raise ValueError(
                "request objective must match accepted implementation scope"
            )

        work_order = self.input_gate.accept(request)

        compiled_plan = self.compiler.compile(work_order)

        workforce_plan = self.workforce_planner.plan_from_requirements(
            work_order_id=work_order.work_order_id,
            objective=work_order.objective,
            requirements=compiled_plan.requirements,
        )

        return ImplementationCompilation(
            scope=scope,
            work_order=work_order,
            compiled_plan=compiled_plan,
            workforce_plan=workforce_plan,
        )


__all__ = [
    "DiagnosticImplementationBridge",
    "ImplementationCompilation",
]
