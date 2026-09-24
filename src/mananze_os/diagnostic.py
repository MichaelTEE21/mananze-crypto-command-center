"""Mananze OS client diagnostic intelligence foundation.

The diagnostic layer interprets tenant-scoped intelligence and produces
an evidence-backed implementation scope. It does not execute actions,
grant authority, modify compiler requirements, or call providers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mananze_os.intelligence_fabric import IntelligenceObservation


DiagnosticSeverity = Literal[
    "info",
    "low",
    "medium",
    "high",
    "critical",
]

DiagnosticCategory = Literal[
    "operations",
    "sales",
    "marketing",
    "revenue",
    "customer_experience",
    "technology",
    "security",
    "compliance",
    "data",
    "integration",
    "cost",
    "workflow",
    "other",
]


@dataclass(frozen=True)
class DiagnosticFinding:
    finding_id: str
    tenant_id: str
    category: DiagnosticCategory
    severity: DiagnosticSeverity
    title: str
    description: str
    evidence_observation_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    recommended_action: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("finding_id", self.finding_id),
            ("tenant_id", self.tenant_id),
            ("title", self.title),
            ("description", self.description),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if not isinstance(self.evidence_observation_ids, tuple):
            raise ValueError("evidence_observation_ids must be a tuple")

        if any(
            not isinstance(item, str) or not item.strip()
            for item in self.evidence_observation_ids
        ):
            raise ValueError(
                "evidence_observation_ids must contain non-empty strings"
            )


@dataclass(frozen=True)
class ImplementationScope:
    tenant_id: str
    objective: str
    recommended_capability_ids: tuple[str, ...] = ()
    required_domains: tuple[str, ...] = ()
    integration_requirements: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    estimated_complexity: Literal["low", "medium", "high"] = "low"

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not self.objective.strip():
            raise ValueError("objective is required")

        for name, values in (
            ("recommended_capability_ids", self.recommended_capability_ids),
            ("required_domains", self.required_domains),
            ("integration_requirements", self.integration_requirements),
            ("risks", self.risks),
            ("dependencies", self.dependencies),
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


@dataclass(frozen=True)
class DiagnosticReport:
    report_id: str
    tenant_id: str
    business_objective: str
    findings: tuple[DiagnosticFinding, ...]
    scope: ImplementationScope
    observation_ids: tuple[str, ...] = ()

    @property
    def high_priority_findings(self) -> tuple[DiagnosticFinding, ...]:
        return tuple(
            finding
            for finding in self.findings
            if finding.severity in ("high", "critical")
        )


class BusinessDiagnostic:
    """Convert tenant-scoped intelligence into an evidence-backed diagnosis."""

    def __init__(self) -> None:
        self._sequence = 0

    def _next_id(self, tenant_id: str) -> str:
        self._sequence += 1
        return f"diagnostic:{tenant_id}:{self._sequence:06d}"

    @staticmethod
    def _category_for_observation(
        observation: IntelligenceObservation,
    ) -> DiagnosticCategory:
        domain = observation.domain.lower()

        known_categories = {
            "operations": "operations",
            "sales": "sales",
            "marketing": "marketing",
            "revenue": "revenue",
            "customer": "customer_experience",
            "customer_experience": "customer_experience",
            "technology": "technology",
            "security": "security",
            "cybersecurity": "security",
            "compliance": "compliance",
            "data": "data",
            "integration": "integration",
            "cost": "cost",
            "workflow": "workflow",
        }

        return known_categories.get(domain, "other")  # type: ignore[return-value]

    @staticmethod
    def _severity_for_observation(
        observation: IntelligenceObservation,
    ) -> DiagnosticSeverity:
        if observation.kind == "gap":
            if observation.confidence >= 0.85:
                return "high"
            if observation.confidence >= 0.60:
                return "medium"
            return "low"

        if observation.kind == "dependency":
            return "medium"

        if observation.kind == "recommendation":
            return "info"

        if observation.status == "conflicting":
            return "medium"

        return "info"

    @staticmethod
    def _description(observation: IntelligenceObservation) -> str:
        value = observation.value

        if isinstance(value, str):
            return value.strip()

        return str(value)

    @staticmethod
    def _capability_recommendation(
        observation: IntelligenceObservation,
    ) -> str | None:
        if observation.kind != "recommendation":
            return None

        if not isinstance(observation.value, dict):
            return None

        capability_id = observation.value.get("capability_id")

        if not isinstance(capability_id, str):
            return None

        capability_id = capability_id.strip()

        return capability_id or None

    def diagnose(
        self,
        *,
        tenant_id: str,
        business_objective: str,
        observations: tuple[IntelligenceObservation, ...],
        report_id: str | None = None,
    ) -> DiagnosticReport:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not business_objective.strip():
            raise ValueError("business_objective is required")

        for observation in observations:
            if observation.tenant_id != tenant_id:
                raise PermissionError(
                    "cross-tenant intelligence access denied"
                )

        findings: list[DiagnosticFinding] = []
        capability_ids: list[str] = []
        domains: list[str] = []
        integrations: list[str] = []
        risks: list[str] = []
        dependencies: list[str] = []

        for observation in observations:
            category = self._category_for_observation(observation)
            severity = self._severity_for_observation(observation)

            if observation.domain not in domains:
                domains.append(observation.domain)

            capability_id = self._capability_recommendation(observation)

            if capability_id and capability_id not in capability_ids:
                capability_ids.append(capability_id)

            if observation.kind == "dependency":
                dependency = self._description(observation)
                if dependency and dependency not in dependencies:
                    dependencies.append(dependency)

            if observation.kind == "gap" and observation.domain == "integration":
                integration = self._description(observation)
                if integration and integration not in integrations:
                    integrations.append(integration)

            if (
                severity in ("high", "critical")
                and observation.kind in ("gap", "dependency")
            ):
                risk = self._description(observation)
                if risk and risk not in risks:
                    risks.append(risk)

            findings.append(
                DiagnosticFinding(
                    finding_id=f"{self._next_id(tenant_id)}:finding",
                    tenant_id=tenant_id,
                    category=category,
                    severity=severity,
                    title=observation.subject,
                    description=self._description(observation),
                    evidence_observation_ids=(observation.observation_id,),
                    confidence=observation.confidence,
                    recommended_action=(
                        f"Evaluate capability '{capability_id}'"
                        if capability_id
                        else None
                    ),
                )
            )

        if not findings:
            complexity: Literal["low", "medium", "high"] = "low"
        elif len(findings) >= 8 or len(risks) >= 3:
            complexity = "high"
        elif len(findings) >= 3 or risks:
            complexity = "medium"
        else:
            complexity = "low"

        scope = ImplementationScope(
            tenant_id=tenant_id,
            objective=business_objective.strip(),
            recommended_capability_ids=tuple(capability_ids),
            required_domains=tuple(domains),
            integration_requirements=tuple(integrations),
            risks=tuple(risks),
            dependencies=tuple(dependencies),
            estimated_complexity=complexity,
        )

        return DiagnosticReport(
            report_id=report_id or self._next_id(tenant_id),
            tenant_id=tenant_id,
            business_objective=business_objective.strip(),
            findings=tuple(findings),
            scope=scope,
            observation_ids=tuple(
                observation.observation_id for observation in observations
            ),
        )


__all__ = [
    "BusinessDiagnostic",
    "DiagnosticFinding",
    "DiagnosticReport",
    "ImplementationScope",
]
