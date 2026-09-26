"""Governed boundary between execution governance and external providers."""

from __future__ import annotations

from dataclasses import dataclass

from mananze_os.governed_execution import GovernedExecutionResult
from mananze_os.provider_router import ProviderRoutingResult
from mananze_os.runtime import ExecutionRequest, RuntimeExecutionBoundary


@dataclass(frozen=True)
class GovernedProviderExecutionResult:
    """Provider result tied directly to an allowed governance decision."""

    governance: GovernedExecutionResult
    provider: ProviderRoutingResult

    @property
    def success(self) -> bool:
        return self.provider.success


class GovernedProviderExecutionBoundary:
    """
    Hard boundary between Mananze governance and external execution.

    Only a completed ``allowed`` GovernedExecutionResult may cross this
    boundary. This class does not perform authorization, policy, approval,
    or provider routing itself. It delegates provider execution to the
    existing RuntimeExecutionBoundary.
    """

    def __init__(self, runtime_boundary: RuntimeExecutionBoundary) -> None:
        if not isinstance(runtime_boundary, RuntimeExecutionBoundary):
            raise TypeError(
                "runtime_boundary must be a RuntimeExecutionBoundary"
            )

        self.runtime_boundary = runtime_boundary

    def execute(
        self,
        governance: GovernedExecutionResult,
    ) -> GovernedProviderExecutionResult:
        if not isinstance(governance, GovernedExecutionResult):
            raise TypeError(
                "governance must be a GovernedExecutionResult"
            )

        if governance.disposition != "allowed":
            raise PermissionError(
                "provider execution requires an allowed governance decision"
            )

        action_request = governance.action_request

        if action_request is None:
            raise ValueError(
                "allowed governance result must contain an action request"
            )

        self._validate_lineage(governance)

        request = ExecutionRequest(
            tenant_id=action_request.tenant_id,
            execution_id=action_request.execution_id,
            tool_id=action_request.tool_id,
            operation=action_request.action,
            payload=dict(action_request.payload),
            authorization_id=(
                f"authorization:{governance.execution_id}"
            ),
            approval_id=self._approval_id(governance),
        )

        provider_result = self.runtime_boundary.execute(request)

        return GovernedProviderExecutionResult(
            governance=governance,
            provider=provider_result,
        )

    @staticmethod
    def _approval_id(
        governance: GovernedExecutionResult,
    ) -> str | None:
        approval = governance.approval

        if approval is None:
            return None

        if approval.status != "approved":
            raise PermissionError(
                "provider execution cannot use a non-approved approval decision"
            )

        if approval.execution_id != governance.execution_id:
            raise ValueError(
                "approval execution does not match governance execution"
            )

        return approval.approval_id

    @staticmethod
    def _validate_lineage(
        governance: GovernedExecutionResult,
    ) -> None:
        request = governance.action_request

        if request is None:
            raise ValueError(
                "governance action request is required"
            )

        if request.execution_id != governance.execution_id:
            raise ValueError(
                "action execution does not match governance execution"
            )

        if request.tenant_id != governance.tenant_id:
            raise ValueError(
                "action tenant does not match governance tenant"
            )

        if request.capability_id != governance.capability_id:
            raise ValueError(
                "action capability does not match governance capability"
            )

        if request.action != governance.action:
            raise ValueError(
                "action does not match governance action"
            )

        if not request.tool_id.strip():
            raise ValueError(
                "provider execution requires an explicit tool_id"
            )


__all__ = [
    "GovernedProviderExecutionBoundary",
    "GovernedProviderExecutionResult",
]
