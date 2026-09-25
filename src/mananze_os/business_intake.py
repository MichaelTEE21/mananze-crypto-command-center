"""Real-business intake and evidence collection foundation for Mananze OS.

Business Twin creation is intentionally outside this module.

Lifecycle:
    CREATED -> COLLECTING -> READY_FOR_ANALYSIS
    -> ANALYSING -> ANALYSIS_COMPLETE -> TWIN_BUILD_READY

Evidence is tenant-scoped and must exist before analysis can begin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from .evidence_reference import EvidenceQuality, EvidenceReference


IntakeStatus = Literal[
    "created",
    "collecting",
    "ready_for_analysis",
    "analysing",
    "analysis_complete",
    "twin_build_ready",
]


_ALLOWED_TRANSITIONS: dict[IntakeStatus, tuple[IntakeStatus, ...]] = {
    "created": ("collecting",),
    "collecting": ("collecting", "ready_for_analysis"),
    "ready_for_analysis": ("analysing",),
    "analysing": ("analysis_complete",),
    "analysis_complete": ("twin_build_ready",),
    "twin_build_ready": (),
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class IntakeEvidence:
    """Evidence supplied during real-business onboarding."""

    evidence_id: str
    tenant_id: str
    source_type: str
    source_reference: str
    quality: EvidenceQuality = "unknown"
    description: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.source_type.strip():
            raise ValueError("source_type is required")
        if not self.source_reference.strip():
            raise ValueError("source_reference is required")

    def to_reference(self) -> EvidenceReference:
        return EvidenceReference(
            evidence_id=self.evidence_id,
            tenant_id=self.tenant_id,
            source_type=self.source_type,
            source_reference=self.source_reference,
            quality=self.quality,
            description=self.description,
        )


@dataclass
class BusinessIntakeCase:
    """Controlled intake case for one real business tenant."""

    intake_id: str
    tenant_id: str
    status: IntakeStatus = "created"
    evidence: list[IntakeEvidence] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.intake_id.strip():
            raise ValueError("intake_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

    def add_evidence(self, item: IntakeEvidence) -> IntakeEvidence:
        if item.tenant_id != self.tenant_id:
            raise PermissionError(
                "evidence tenant does not match intake tenant"
            )

        if any(
            existing.evidence_id == item.evidence_id
            for existing in self.evidence
        ):
            raise ValueError(
                f"evidence_id already exists in intake: {item.evidence_id}"
            )

        self.evidence.append(item)
        self.updated_at = _utc_now()

        if self.status == "created":
            self.status = "collecting"

        return item

    def transition(self, new_status: IntakeStatus) -> IntakeStatus:
        # These checks deliberately happen before the generic transition
        # check so the caller receives the actual reason the transition
        # cannot happen.
        if new_status == "ready_for_analysis" and not self.evidence:
            raise ValueError(
                "cannot mark intake ready for analysis without evidence"
            )

        if new_status == "twin_build_ready" and self.status != "analysis_complete":
            raise ValueError(
                "business twin cannot be prepared before analysis is complete"
            )

        allowed = _ALLOWED_TRANSITIONS[self.status]

        if new_status not in allowed:
            raise ValueError(
                f"invalid intake transition: "
                f"{self.status} -> {new_status}"
            )

        self.status = new_status
        self.updated_at = _utc_now()
        return self.status

    def evidence_references(self) -> tuple[EvidenceReference, ...]:
        return tuple(item.to_reference() for item in self.evidence)


__all__ = [
    "BusinessIntakeCase",
    "IntakeEvidence",
    "IntakeStatus",
]
