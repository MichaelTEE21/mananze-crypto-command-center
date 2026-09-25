
"""Governed Business Truth resolution for Mananze OS.

Business Truth sits between observed intelligence and the Business Twin.

It does not:
- invent facts
- silently resolve conflicting evidence
- authorize actions
- activate capabilities
- execute external actions

It resolves evidence-backed observations into tenant-scoped truth records.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from .intelligence_fabric import IntelligenceObservation


TruthStatus = Literal[
    "established",
    "conflicting",
    "stale",
    "inferred",
    "unresolved",
]

SourceType = Literal[
    "human_confirmed",
    "official_document",
    "business_document",
    "website",
    "system",
    "observation",
    "inference",
    "unknown",
]


_SOURCE_PRECEDENCE: dict[SourceType, int] = {
    "human_confirmed": 100,
    "official_document": 90,
    "business_document": 80,
    "system": 70,
    "website": 60,
    "observation": 50,
    "inference": 20,
    "unknown": 0,
}


@dataclass(frozen=True)
class TruthCandidate:
    """A proposed business fact backed by an intelligence observation."""

    observation: IntelligenceObservation
    source_type: SourceType = "unknown"
    effective_at: datetime | None = None
    source_quality: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.source_quality <= 1.0:
            raise ValueError("source_quality must be between 0.0 and 1.0")

        if self.effective_at is not None and not isinstance(
            self.effective_at, datetime
        ):
            raise ValueError("effective_at must be datetime or None")


@dataclass(frozen=True)
class BusinessTruth:
    """Tenant-scoped resolved business truth."""

    truth_id: str
    tenant_id: str
    subject: str
    value: object
    status: TruthStatus
    confidence: float
    source_type: SourceType
    source_reference: str | None
    observation_ids: tuple[str, ...]
    effective_at: datetime | None
    resolved_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    conflict_observation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (
            ("truth_id", self.truth_id),
            ("tenant_id", self.tenant_id),
            ("subject", self.subject),
            ("source_type", self.source_type),
        )

        for name, value in required:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        for name, values in (
            ("observation_ids", self.observation_ids),
            ("conflict_observation_ids", self.conflict_observation_ids),
        ):
            if not isinstance(values, tuple):
                raise ValueError(f"{name} must be a tuple")

            if any(
                not isinstance(item, str) or not item.strip()
                for item in values
            ):
                raise ValueError(
                    f"{name} must contain non-empty strings"
                )


def _canonical_value(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )


def _truth_id(
    tenant_id: str,
    subject: str,
    value: object,
) -> str:
    material = (
        f"{tenant_id}|{subject}|{_canonical_value(value)}"
    ).encode("utf-8")

    return hashlib.sha256(material).hexdigest()


def _candidate_score(candidate: TruthCandidate) -> tuple[int, float, float]:
    observation = candidate.observation

    return (
        _SOURCE_PRECEDENCE[candidate.source_type],
        candidate.source_quality,
        observation.confidence,
    )


class BusinessTruthResolver:
    """Resolve observations into governed tenant-scoped business truth."""

    def __init__(self) -> None:
        self._truth: dict[str, BusinessTruth] = {}

    def resolve(
        self,
        candidates: tuple[TruthCandidate, ...],
        *,
        tenant_id: str,
    ) -> tuple[BusinessTruth, ...]:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

        for candidate in candidates:
            if candidate.observation.tenant_id != tenant_id:
                raise PermissionError(
                    "cross-tenant business truth resolution denied"
                )

        grouped: dict[str, list[TruthCandidate]] = {}

        for candidate in candidates:
            grouped.setdefault(
                candidate.observation.subject,
                [],
            ).append(candidate)

        resolved: list[BusinessTruth] = []

        for subject, subject_candidates in grouped.items():
            values: dict[str, list[TruthCandidate]] = {}

            for candidate in subject_candidates:
                values.setdefault(
                    _canonical_value(candidate.observation.value),
                    [],
                ).append(candidate)

            if len(values) > 1:
                truth = self._resolve_conflict(
                    subject,
                    subject_candidates,
                    tenant_id,
                )
            else:
                truth = self._resolve_agreement(
                    subject,
                    subject_candidates,
                    tenant_id,
                )

            self._truth[truth.truth_id] = truth
            resolved.append(truth)

        return tuple(resolved)

    def get(
        self,
        truth_id: str,
        *,
        tenant_id: str,
    ) -> BusinessTruth:
        truth = self._truth.get(truth_id)

        if truth is None:
            raise KeyError(truth_id)

        if truth.tenant_id != tenant_id:
            raise PermissionError(
                "cross-tenant business truth access denied"
            )

        return truth

    def list_tenant(
        self,
        tenant_id: str,
    ) -> tuple[BusinessTruth, ...]:
        return tuple(
            truth
            for truth in self._truth.values()
            if truth.tenant_id == tenant_id
        )

    def _resolve_agreement(
        self,
        subject: str,
        candidates: list[TruthCandidate],
        tenant_id: str,
    ) -> BusinessTruth:
        winner = max(candidates, key=_candidate_score)

        confidence = max(
            min(
                winner.observation.confidence
                * max(winner.source_quality, 0.01),
                1.0,
            ),
            0.0,
        )

        status: TruthStatus

        if winner.observation.status == "inferred":
            status = "inferred"
        elif (
            winner.observation.expires_at is not None
            and winner.observation.expires_at
            <= datetime.now(timezone.utc)
        ):
            status = "stale"
        else:
            status = "established"

        truth = BusinessTruth(
            truth_id=_truth_id(
                tenant_id,
                subject,
                winner.observation.value,
            ),
            tenant_id=tenant_id,
            subject=subject,
            value=winner.observation.value,
            status=status,
            confidence=confidence,
            source_type=winner.source_type,
            source_reference=winner.observation.source_reference,
            observation_ids=tuple(
                candidate.observation.observation_id
                for candidate in candidates
            ),
            effective_at=winner.effective_at,
        )

        return truth

    def _resolve_conflict(
        self,
        subject: str,
        candidates: list[TruthCandidate],
        tenant_id: str,
    ) -> BusinessTruth:
        """Preserve the conflict instead of silently choosing a value."""

        winner = max(candidates, key=_candidate_score)

        return BusinessTruth(
            truth_id=_truth_id(
                tenant_id,
                subject,
                "__conflict__",
            ),
            tenant_id=tenant_id,
            subject=subject,
            value={
                "conflict": True,
                "candidates": [
                    {
                        "observation_id": candidate.observation.observation_id,
                        "value": candidate.observation.value,
                        "source_type": candidate.source_type,
                        "source_reference": (
                            candidate.observation.source_reference
                        ),
                        "confidence": candidate.observation.confidence,
                    }
                    for candidate in candidates
                ],
            },
            status="conflicting",
            confidence=winner.observation.confidence,
            source_type=winner.source_type,
            source_reference=winner.observation.source_reference,
            observation_ids=tuple(
                candidate.observation.observation_id
                for candidate in candidates
            ),
            effective_at=winner.effective_at,
            conflict_observation_ids=tuple(
                candidate.observation.observation_id
                for candidate in candidates
            ),
        )


__all__ = [
    "BusinessTruth",
    "BusinessTruthResolver",
    "SourceType",
    "TruthCandidate",
    "TruthStatus",
]
