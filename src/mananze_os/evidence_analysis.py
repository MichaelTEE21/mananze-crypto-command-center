"""Governed evidence analysis boundary for Mananze OS.

Evidence analysis converts supplied business evidence into proposed
intelligence observations.

It does not:
- create a Business Twin
- activate capabilities
- authorize actions
- mark evidence as verified
- modify authoritative business state
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol

from .evidence_reference import EvidenceReference
from .intelligence_fabric import (
    IntelligenceKind,
    IntelligenceObservation,
    IntelligenceStatus,
)


@dataclass(frozen=True)
class EvidenceAnalysisRequest:
    """Evidence plus its content presented to an analysis provider."""

    tenant_id: str
    evidence: EvidenceReference
    content: object

    def __post_init__(self) -> None:
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

        if self.evidence.tenant_id != self.tenant_id:
            raise PermissionError(
                "evidence tenant does not match analysis tenant"
            )


@dataclass(frozen=True)
class EvidenceObservationProposal:
    """An observation proposed by an analysis provider."""

    domain: str
    kind: IntelligenceKind
    subject: str
    value: object
    confidence: float
    status: IntelligenceStatus = "observed"
    related_observation_ids: tuple[str, ...] = ()
    dependency_observation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("domain", self.domain),
            ("subject", self.subject),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


class EvidenceAnalysisProvider(Protocol):
    """Provider contract for evidence analysis."""

    @property
    def provider_id(self) -> str:
        ...

    def analyze(
        self,
        request: EvidenceAnalysisRequest,
    ) -> tuple[EvidenceObservationProposal, ...]:
        ...


def _canonical_value(value: object) -> str:
    """Create stable representation for deterministic observation IDs."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
    except (TypeError, ValueError):
        return repr(value)


def _observation_id(
    *,
    tenant_id: str,
    evidence_id: str,
    provider_id: str,
    proposal: EvidenceObservationProposal,
) -> str:
    material = "|".join(
        (
            tenant_id,
            evidence_id,
            provider_id,
            proposal.domain,
            proposal.kind,
            proposal.subject,
            _canonical_value(proposal.value),
        )
    )

    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()

    return f"obs:evidence:{digest[:32]}"


class EvidenceAnalysisEngine:
    """Governed boundary between evidence and intelligence observations."""

    def __init__(self, provider: EvidenceAnalysisProvider) -> None:
        self.provider = provider

    def analyze(
        self,
        request: EvidenceAnalysisRequest,
    ) -> tuple[IntelligenceObservation, ...]:
        if request.tenant_id != request.evidence.tenant_id:
            raise PermissionError(
                "cross-tenant evidence analysis denied"
            )

        provider_id = self.provider.provider_id

        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("analysis provider_id must be a non-empty string")

        proposals = self.provider.analyze(request)

        observations: list[IntelligenceObservation] = []

        for proposal in proposals:
            if proposal.status == "verified":
                raise PermissionError(
                    "evidence analysis cannot mark observations as verified"
                )

            observation = IntelligenceObservation(
                observation_id=_observation_id(
                    tenant_id=request.tenant_id,
                    evidence_id=request.evidence.evidence_id,
                    provider_id=provider_id,
                    proposal=proposal,
                ),
                tenant_id=request.tenant_id,
                domain=proposal.domain,
                kind=proposal.kind,
                subject=proposal.subject,
                value=proposal.value,
                status=proposal.status,
                confidence=proposal.confidence,
                source_reference=request.evidence.source_reference,
                related_observation_ids=proposal.related_observation_ids,
                dependency_observation_ids=proposal.dependency_observation_ids,
            )

            observations.append(observation)

        return tuple(observations)


class StaticEvidenceAnalysisProvider:
    """Deterministic provider used for tests and controlled integrations.

    Real parsers, LLM providers, OCR systems, or document-analysis services
    can later implement the same EvidenceAnalysisProvider contract.
    """

    def __init__(
        self,
        proposals: tuple[EvidenceObservationProposal, ...],
        *,
        provider_id: str = "static-evidence-analysis",
    ) -> None:
        if not provider_id.strip():
            raise ValueError("provider_id must not be blank")

        self._provider_id = provider_id
        self._proposals = proposals

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def analyze(
        self,
        request: EvidenceAnalysisRequest,
    ) -> tuple[EvidenceObservationProposal, ...]:
        return self._proposals


__all__ = [
    "EvidenceAnalysisEngine",
    "EvidenceAnalysisProvider",
    "EvidenceAnalysisRequest",
    "EvidenceObservationProposal",
    "StaticEvidenceAnalysisProvider",
]
