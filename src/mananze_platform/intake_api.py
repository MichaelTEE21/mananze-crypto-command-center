"""Public Platform intake API."""
from __future__ import annotations

from mananze_platform.capability_discovery import (
    CapabilityCandidate,
    discover_capabilities,
)
from mananze_platform.intake import (
    BusinessIntake,
    BusinessObservation,
    IntakeAnalysis,
    IntakeSource,
    ObservationType,
    analyse_intake,
)


def process_business_intake(
    intake: BusinessIntake,
) -> tuple[IntakeAnalysis, tuple[CapabilityCandidate, ...]]:
    """Analyse submitted information and discover candidate Hub services.

    No execution occurs here.
    """
    analysis = analyse_intake(intake)
    candidates = discover_capabilities(analysis.observations)
    return analysis, candidates


__all__ = [
    "BusinessIntake",
    "BusinessObservation",
    "CapabilityCandidate",
    "IntakeAnalysis",
    "IntakeSource",
    "ObservationType",
    "analyse_intake",
    "discover_capabilities",
    "process_business_intake",
]
