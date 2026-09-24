"""Mananze Platform -> Mananze OS integration boundary.

The Platform owns customer intake and experience.
Mananze OS remains authoritative for planning, policy, authorization,
QA, approval, execution, evidence, and verification.

This adapter performs translation only. It does not implement a second
compiler, orchestrator, workforce engine, policy engine, or executor.
"""

from dataclasses import dataclass

from mananze_os.authority import Authority
from mananze_os.input_request import InputRequest
from mananze_os.runtime import MananzeRuntime, RuntimeResult
from mananze_os.tenant import Tenant

from .capability_discovery import (
    CapabilityCandidate,
    resolve_os_capability_candidates,
)
from .intake import BusinessIntake


@dataclass(frozen=True)
class PlatformRuntimeRequest:
    """Validated Platform request prepared for the OS."""

    tenant: Tenant
    authority: Authority
    intake: BusinessIntake
    objective: str
    capability_candidates: tuple[CapabilityCandidate, ...] = ()

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")

        if self.tenant.tenant_id != self.intake.tenant_id:
            raise ValueError("tenant_id mismatch between tenant and intake")

        if self.authority.actor_id != self.intake.actor_id:
            raise ValueError("actor_id mismatch between authority and intake")


def to_input_request(request: PlatformRuntimeRequest) -> InputRequest:
    """Translate a Platform request into the OS input contract."""
    candidate_capability_ids = resolve_os_capability_candidates(
        request.capability_candidates
    )

    return InputRequest(
        request_id=request.intake.intake_id,
        tenant_id=request.tenant.tenant_id,
        actor_id=request.authority.actor_id,
        objective=request.objective.strip(),
        channel=request.intake.source.value,
        processing_mode="standard",
        candidate_capability_ids=candidate_capability_ids,
    )


def prepare_platform_request(
    runtime: MananzeRuntime,
    request: PlatformRuntimeRequest,
) -> RuntimeResult:
    """Submit a Platform request to the authoritative OS runtime."""
    input_request = to_input_request(request)
    return runtime.prepare(input_request)


__all__ = [
    "PlatformRuntimeRequest",
    "prepare_platform_request",
    "to_input_request",
]
