"""Tenant business intake contracts for the Mananze Platform.

The Platform collects information.
The Hub supplies capabilities.
Mananze OS remains responsible for governance, authorization and execution.

This module does not execute business actions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Mapping
from uuid import uuid4


class IntakeSource(StrEnum):
    BUSINESS_DESCRIPTION = "business_description"
    DOCUMENT = "document"
    WEBSITE = "website"
    COMMUNICATION = "communication"


class ObservationType(StrEnum):
    BUSINESS_IDENTITY = "business_identity"
    BUSINESS_ACTIVITY = "business_activity"
    OPERATIONAL_NEED = "operational_need"
    COMMERCIAL_NEED = "commercial_need"
    RISK = "risk"
    CUSTOMER_SERVICE = "customer_service"
    DATA = "data"
    OTHER = "other"


@dataclass(frozen=True)
class BusinessIntake:
    """Tenant-scoped information submitted to Mananze."""

    tenant_id: str
    actor_id: str
    source: IntakeSource
    content: str
    intake_id: str = field(default_factory=lambda: f"intake:{uuid4().hex}")
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.actor_id.strip():
            raise ValueError("actor_id is required")
        if not self.content.strip():
            raise ValueError("content is required")


@dataclass(frozen=True)
class BusinessObservation:
    """A structured fact or signal extracted from tenant information."""

    tenant_id: str
    intake_id: str
    observation_type: ObservationType
    statement: str
    source: IntakeSource
    confidence: float = 1.0
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.intake_id.strip():
            raise ValueError("intake_id is required")
        if not self.statement.strip():
            raise ValueError("statement is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class IntakeAnalysis:
    """Read-only structured result passed toward capability discovery."""

    tenant_id: str
    intake_id: str
    observations: tuple[BusinessObservation, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)


def analyse_intake(intake: BusinessIntake) -> IntakeAnalysis:
    """Create conservative observations without inventing business facts.

    This first implementation deliberately preserves the submitted content as
    evidence rather than pretending to perform semantic extraction. A later
    intelligence capability can produce richer observations through the OS.
    """
    observation = BusinessObservation(
        tenant_id=intake.tenant_id,
        intake_id=intake.intake_id,
        observation_type=ObservationType.OTHER,
        statement=intake.content.strip(),
        source=intake.source,
        confidence=1.0,
        evidence_ref=intake.intake_id,
    )

    return IntakeAnalysis(
        tenant_id=intake.tenant_id,
        intake_id=intake.intake_id,
        observations=(observation,),
        metadata={
            "source": intake.source.value,
            "analysis_mode": "evidence_preserving",
        },
    )
