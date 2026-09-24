"""Mananze Hub capability catalog.

The Hub is a declarative capability ecosystem. It describes capabilities
that may be made available to Mananze OS.

The Hub does not execute work, approve actions, authorize access, route
providers, or replace Mananze OS. The OS remains authoritative for
validation, governance, planning, authorization, execution, evidence,
and verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


CapabilityLifecycle = Literal[
    "draft",
    "validated",
    "available",
    "deprecated",
]

CapabilityRisk = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


@dataclass(frozen=True)
class HubCapability:
    """Declarative manifest describing a Mananze Hub capability."""

    capability_id: str
    name: str
    description: str

    status: CapabilityLifecycle = "available"
    version: str = "1.0.0"

    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

    risk: CapabilityRisk = "medium"
    supported_channels: tuple[str, ...] = (
        "web",
        "whatsapp",
        "telegram",
        "email",
        "voice",
    )

    evidence_requirements: tuple[str, ...] = ()

    os_capability_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.capability_id.strip():
            raise ValueError("capability_id is required")

        if not self.name.strip():
            raise ValueError("name is required")

        if not self.description.strip():
            raise ValueError("description is required")

        if not self.version.strip():
            raise ValueError("version is required")

        self._validate_unique("inputs", self.inputs)
        self._validate_unique("outputs", self.outputs)
        self._validate_unique("dependencies", self.dependencies)
        self._validate_unique("permissions", self.permissions)
        self._validate_unique("supported_channels", self.supported_channels)
        self._validate_unique("evidence_requirements", self.evidence_requirements)
        self._validate_unique("os_capability_ids", self.os_capability_ids)

    @staticmethod
    def _validate_unique(name: str, values: tuple[str, ...]) -> None:
        if any(not value.strip() for value in values):
            raise ValueError(f"{name} cannot contain blank values")

        if len(values) != len(set(values)):
            raise ValueError(f"{name} cannot contain duplicates")


CAPABILITIES: Final[tuple[HubCapability, ...]] = (
    HubCapability(
        "mananze:crypto_web3",
        "Crypto & Web3",
        "Crypto, blockchain and Web3 research capabilities.",
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:marketing",
        "Marketing",
        "Marketing analysis, planning and content capabilities.",
        inputs=("business_profile", "customer_context", "marketing_objective"),
        outputs=("marketing_plan", "content_plan", "campaign_recommendations"),
        permissions=("business_data:read", "marketing:manage"),
        risk="medium",
        evidence_requirements=("source_inputs", "generated_outputs"),
        os_capability_ids=("marketing",),
    ),
    HubCapability(
        "mananze:sales",
        "Sales",
        "Sales analysis, pipeline and customer-conversion capabilities.",
        inputs=("business_profile", "lead_data", "sales_objective"),
        outputs=("sales_plan", "lead_actions", "sales_report"),
        dependencies=("mananze:marketing",),
        permissions=("customer_data:read", "sales:manage"),
        risk="high",
        evidence_requirements=("source_inputs", "action_results"),
        os_capability_ids=("sales",),
    ),
    HubCapability(
        "mananze:revenue",
        "Revenue",
        "Revenue analysis, opportunities and commercial optimisation.",
        inputs=("business_profile", "sales_data", "revenue_objective"),
        outputs=("revenue_analysis", "revenue_opportunities"),
        dependencies=("mananze:sales",),
        permissions=("business_data:read", "revenue:manage"),
        risk="high",
        evidence_requirements=("source_inputs", "analysis_results"),
        os_capability_ids=("revenue",),
    ),
    HubCapability(
        "mananze:finance",
        "Finance",
        "Business finance analysis and financial-operational intelligence.",
        inputs=("business_profile", "financial_data"),
        outputs=("financial_analysis", "financial_report"),
        permissions=("financial_data:read",),
        risk="critical",
        evidence_requirements=("source_documents", "analysis_results"),
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:cybersecurity",
        "Cybersecurity",
        "Cybersecurity assessment, monitoring and response capabilities.",
        inputs=("business_profile", "security_context"),
        outputs=("security_assessment", "security_recommendations"),
        permissions=("security_data:read",),
        risk="critical",
        evidence_requirements=("source_evidence", "assessment_results"),
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:legal",
        "Legal",
        "Legal-information and business-compliance capabilities.",
        inputs=("business_profile", "legal_context", "documents"),
        outputs=("legal_information", "compliance_report"),
        permissions=("legal_data:read",),
        risk="critical",
        evidence_requirements=("source_documents", "legal_sources"),
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:data_analytics",
        "Data & Analytics",
        "Business data analysis and intelligence capabilities.",
        inputs=("business_profile", "business_data"),
        outputs=("analysis", "insights", "reports"),
        permissions=("business_data:read",),
        risk="medium",
        evidence_requirements=("source_data", "analysis_results"),
        os_capability_ids=("reporting",),
    ),
    HubCapability(
        "mananze:customer_service",
        "Customer Service",
        "Customer communication and service-operation capabilities.",
        inputs=("business_profile", "customer_context", "service_requests"),
        outputs=("customer_responses", "service_report"),
        permissions=("customer_data:read", "customer_communications:manage"),
        risk="high",
        supported_channels=(
            "web",
            "whatsapp",
            "telegram",
            "email",
            "voice",
        ),
        evidence_requirements=("customer_request", "communication_result"),
        os_capability_ids=(
            "customer_communications",
            "retention",
            "reporting",
        ),
    ),
    HubCapability(
        "mananze:logistics",
        "Logistics",
        "Logistics planning and operational capabilities.",
        inputs=("business_profile", "orders", "fleet_context", "delivery_requirements"),
        outputs=("logistics_plan", "route_recommendations", "operations_report"),
        permissions=("operations_data:read", "logistics:manage"),
        risk="high",
        evidence_requirements=("source_inputs", "planning_results", "action_results"),
        os_capability_ids=(
            "logistics",
            "fleet",
            "cost_analysis",
            "revenue",
            "reporting",
        ),
    ),
    HubCapability(
        "mananze:property",
        "Property",
        "Property and property-business capabilities.",
        inputs=("business_profile", "property_data"),
        outputs=("property_analysis", "property_report"),
        permissions=("property_data:read",),
        risk="high",
        evidence_requirements=("source_data", "analysis_results"),
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:construction",
        "Construction",
        "Construction-business planning and operational capabilities.",
        inputs=("business_profile", "project_data", "site_context"),
        outputs=("project_plan", "operations_report"),
        permissions=("operations_data:read", "project_data:manage"),
        risk="high",
        evidence_requirements=("source_documents", "project_results"),
        os_capability_ids=("operations", "reporting"),
    ),
)


def list_capabilities() -> tuple[HubCapability, ...]:
    """Return the capabilities currently available to Mananze OS."""
    return CAPABILITIES


def get_capability(capability_id: str) -> HubCapability | None:
    """Return a capability by ID without executing anything."""
    return next(
        (
            capability
            for capability in CAPABILITIES
            if capability.capability_id == capability_id
        ),
        None,
    )


__all__ = [
    "CapabilityLifecycle",
    "CapabilityRisk",
    "HubCapability",
    "CAPABILITIES",
    "list_capabilities",
    "get_capability",
]
