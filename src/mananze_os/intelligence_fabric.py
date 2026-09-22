from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


IntelligenceStatus = Literal[
    "observed",
    "verified",
    "conflicting",
    "inferred",
    "stale",
    "rejected",
]

IntelligenceKind = Literal[
    "fact",
    "signal",
    "relationship",
    "dependency",
    "gap",
    "recommendation",
]


@dataclass(frozen=True)
class IntelligenceObservation:
    observation_id: str
    tenant_id: str
    domain: str
    kind: IntelligenceKind
    subject: str
    value: object
    status: IntelligenceStatus = "observed"
    confidence: float = 0.0
    source_reference: str | None = None
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: datetime | None = None
    related_observation_ids: tuple[str, ...] = ()
    dependency_observation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (
            ("observation_id", self.observation_id),
            ("tenant_id", self.tenant_id),
            ("domain", self.domain),
            ("kind", self.kind),
            ("subject", self.subject),
        )
        for name, value in required:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if self.source_reference is not None:
            if not isinstance(self.source_reference, str):
                raise ValueError("source_reference must be a string or None")

        for name, values in (
            ("related_observation_ids", self.related_observation_ids),
            ("dependency_observation_ids", self.dependency_observation_ids),
        ):
            if not isinstance(values, tuple):
                raise ValueError(f"{name} must be a tuple")
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ValueError(f"{name} must contain non-empty strings")


@dataclass(frozen=True)
class IntelligenceQuery:
    tenant_id: str
    domains: tuple[str, ...] = ()
    kinds: tuple[IntelligenceKind, ...] = ()
    statuses: tuple[IntelligenceStatus, ...] = ()
    subject: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")


class IntelligenceFabric:
    """Tenant-scoped shared substrate for Mananze intelligence."""

    def __init__(self) -> None:
        self._observations: dict[str, IntelligenceObservation] = {}

    def publish(self, observation: IntelligenceObservation) -> None:
        if observation.observation_id in self._observations:
            raise ValueError(
                f"observation already exists: {observation.observation_id}"
            )

        self._observations[observation.observation_id] = observation

    def get(
        self,
        observation_id: str,
        *,
        tenant_id: str,
    ) -> IntelligenceObservation:
        observation = self._observations.get(observation_id)

        if observation is None:
            raise KeyError(observation_id)

        if observation.tenant_id != tenant_id:
            raise PermissionError("cross-tenant intelligence access denied")

        return observation

    def query(
        self,
        query: IntelligenceQuery,
    ) -> tuple[IntelligenceObservation, ...]:
        results = []

        for observation in self._observations.values():
            if observation.tenant_id != query.tenant_id:
                continue

            if query.domains and observation.domain not in query.domains:
                continue

            if query.kinds and observation.kind not in query.kinds:
                continue

            if query.statuses and observation.status not in query.statuses:
                continue

            if (
                query.subject is not None
                and observation.subject != query.subject
            ):
                continue

            results.append(observation)

        return tuple(results)

    def list_tenant(
        self,
        tenant_id: str,
    ) -> tuple[IntelligenceObservation, ...]:
        return self.query(IntelligenceQuery(tenant_id=tenant_id))
