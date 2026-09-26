"""Independent runtime/provider execution contracts."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.provider_router import ProviderRouter

@dataclass(frozen=True)
class ExecutionRequest:
    """Request passed from governed runtime execution into provider routing."""

    tenant_id: str
    execution_id: str
    tool_id: str
    operation: str
    payload: dict
    authorization_id: str
    approval_id: str | None = None

    def __post_init__(self) -> None:
        fields = {
            "tenant_id": self.tenant_id,
            "execution_id": self.execution_id,
            "tool_id": self.tool_id,
            "operation": self.operation,
            "authorization_id": self.authorization_id,
        }

        for name, value in fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")

        if self.approval_id is not None:
            if not isinstance(self.approval_id, str) or not self.approval_id.strip():
                raise ValueError("approval_id cannot be blank")

        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a dict")


class RuntimeExecutionBoundary:
    """Controlled bridge from MananzeRuntime into ProviderRouter."""

    def __init__(self, router: ProviderRouter) -> None:
        if not isinstance(router, ProviderRouter):
            raise TypeError("router must be a ProviderRouter")
        self.router = router

    def execute(self, request: ExecutionRequest) -> ProviderRoutingResult:
        if not isinstance(request, ExecutionRequest):
            raise TypeError("request must be an ExecutionRequest")

        return self.router.route(
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            operation=request.operation,
            payload=request.payload,
        )


@dataclass(frozen=True)
class RuntimeReport:
    work_order_id: str
    execution_id: str
    status: str
    evidence: tuple[ExecutionEvidence, ...]
    verification: ExecutionVerification


@dataclass(frozen=True)
class RuntimeResult:
    work_order: WorkOrder
    plan: CompiledPlan
    workforce: DynamicWorkforcePlan
    policy: PolicyDecision
    authorization: AuthorizationDecision
    qa: QAVerdict
    quality: QualityAssessment
    action_gate: ActionGateDecision
    approval: ApprovalDecision
    execution_state: ExecutionState
    request_state: RequestState
    report: RuntimeReport | None = None


@dataclass(frozen=True)
class RuntimeGovernedPlan:
    """Runtime execution plan used by governed execution boundaries."""

    tenant_id: str
    twin_id: str
    work_order_id: str
    objective: str
    selections: tuple[WorkforceSelection, ...]
    dynamic_plan: DynamicWorkforcePlan
    execution_graph: ExecutionGraph

