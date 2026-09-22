"""Mananze OS evidence reference and obligation candidate validation foundation."""

from dataclasses import dataclass
from typing import Literal

from mananze_os.recurring_expense_intelligence import ObligationCandidate


EvidenceQuality = Literal[
    "unknown",
    "weak",
    "moderate",
    "strong",
]


@dataclass(frozen=True)
class EvidenceReference:
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
        if not self.quality.strip():
            raise ValueError("quality is required")


@dataclass(frozen=True)
class ObligationCandidateValidation:
    tenant_id: str
    candidate_name: str
    evidence_count: int
    evidence_ids: tuple[str, ...]
    status: Literal[
        "insufficient_evidence",
        "supported",
        "conflicting_evidence",
    ]
    reason: str

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.candidate_name.strip():
            raise ValueError("candidate_name is required")
        if self.evidence_count < 0:
            raise ValueError("evidence_count cannot be negative")
        if not self.status.strip():
            raise ValueError("status is required")
        if not self.reason.strip():
            raise ValueError("reason is required")


class ObligationCandidateValidator:
    """Validate obligation candidates against supplied evidence references.

    Validation supports promotion decisions but never authorises payment,
    execution, or changes to authoritative state.
    """

    def validate(
        self,
        candidate: ObligationCandidate,
        evidence: tuple[EvidenceReference, ...],
    ) -> ObligationCandidateValidation:
        candidate_evidence = tuple(
            item
            for item in evidence
            if item.tenant_id == candidate.tenant_id
            and item.evidence_id in candidate.evidence_expense_ids
        )

        conflicting = any(
            item.quality == "unknown"
            for item in candidate_evidence
        )

        if conflicting:
            status = "conflicting_evidence"
            reason = "Candidate evidence contains unresolved evidence quality."

        elif len(candidate_evidence) == 0:
            status = "insufficient_evidence"
            reason = "No matching tenant-scoped evidence was supplied."

        else:
            status = "supported"
            reason = "Candidate is supported by tenant-scoped evidence."

        return ObligationCandidateValidation(
            tenant_id=candidate.tenant_id,
            candidate_name=candidate.name,
            evidence_count=len(candidate_evidence),
            evidence_ids=tuple(
                item.evidence_id for item in candidate_evidence
            ),
            status=status,
            reason=reason,
        )


__all__ = [
    "EvidenceQuality",
    "EvidenceReference",
    "ObligationCandidateValidation",
    "ObligationCandidateValidator",
]
