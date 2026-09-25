"""Canonical Mananze AI workforce catalog.

Defines the 20 Domain Orchestrators and 180 Specialist roles that make up
the Mananze workforce. Workforce roles describe capability and responsibility;
they do not grant authority or execution permission.
"""

from mananze_os.capability_registry import (
    Capability,
    CapabilityRegistry,
    default_capability_registry,
)
from mananze_os.skill import Skill
from mananze_os.skill_registry import SkillRegistry, default_skill_registry
from mananze_os.workforce_registry import WorkforceRegistry
from mananze_os.workforce_role import WorkforceRole
from mananze_os.workforce_role_validator import WorkforceRoleValidator


DOMAIN_DEFINITIONS = (
    ("marketing", "Marketing & Growth", "marketing"),
    ("sales", "Sales", "sales"),
    ("revenue", "Revenue & Economics", "revenue"),
    ("customer", "Customer Success", "customer_communications"),
    ("communications", "Communications", "customer_communications"),
    ("operations", "Operations", "operations"),
    ("logistics", "Logistics", "logistics"),
    ("fleet", "Fleet & Mobility", "fleet"),
    ("finance", "Finance", "cost_analysis"),
    ("intelligence", "Intelligence & Research", "reporting"),
    ("data", "Data & Analytics", "reporting"),
    ("legal", "Legal", "reporting"),
    ("compliance", "Compliance", "reporting"),
    ("cybersecurity", "Cybersecurity", "operations"),
    ("risk", "Risk & Fraud", "cost_analysis"),
    ("technology", "Technology & Engineering", "operations"),
    ("property", "Property & Construction", "operations"),
    ("public_services", "Solve SA & Public Services", "operations"),
    ("physical_systems", "Physical Systems & Emerging Operations", "logistics"),
    ("strategy", "Strategy & Business Intelligence", "reporting"),
)


ORCHESTRATOR_NAMES = (
    "Maven",
    "Kairo",
    "Vela",
    "Nexus",
    "Crest",
    "Sage",
    "Pulse",
    "Vector",
    "Beacon",
    "Forge",
    "Axiom",
    "Prism",
    "Helix",
    "Cipher",
    "Summit",
    "Relay",
    "Terra",
    "Civic",
    "Quanta",
    "Catalyst",
)


SPECIALIST_NAME_SEEDS = (
    "Analyst",
    "Planner",
    "Coordinator",
    "Researcher",
    "Strategist",
    "Optimizer",
    "Monitor",
    "Reviewer",
    "Advisor",
)


def _ensure_extended_capabilities(registry: CapabilityRegistry) -> None:
    """Add domain capabilities while preserving the existing catalog."""

    existing = {item.capability_id for item in registry.list_all()}

    definitions = (
        ("customer_success", "Customer Success", "Manage controlled customer success workflows.", ("business", "customer")),
        ("communications", "Communications", "Coordinate approved communications workflows.", ("business", "communications")),
        ("finance", "Finance", "Analyse controlled financial operations.", ("business", "finance")),
        ("accounting_tax", "Accounting & Tax", "Support accounting and tax information workflows.", ("business", "finance", "compliance")),
        ("legal", "Legal", "Support controlled legal research and document workflows.", ("business", "legal", "compliance")),
        ("compliance", "Compliance", "Monitor compliance obligations and evidence.", ("business", "compliance", "risk")),
        ("cybersecurity", "Cybersecurity", "Analyse security posture and security events.", ("technology", "security", "risk")),
        ("risk_fraud", "Risk & Fraud", "Analyse operational risk and fraud indicators.", ("business", "risk", "security")),
        ("intelligence", "Intelligence", "Produce structured research and intelligence.", ("intelligence", "research")),
        ("data_analytics", "Data & Analytics", "Analyse structured and unstructured business data.", ("intelligence", "data")),
        ("technology", "Technology & Engineering", "Coordinate technology and engineering workflows.", ("technology", "engineering")),
        ("property_construction", "Property & Construction", "Support property and construction workflows.", ("business", "property", "construction")),
        ("public_services", "Public Services", "Coordinate public-interest service workflows.", ("public_services", "customer")),
        ("physical_systems", "Physical Systems", "Support controlled physical-world operational workflows.", ("operations", "logistics", "physical")),
        ("strategy", "Strategy", "Support strategic planning and business intelligence.", ("business", "strategy", "intelligence")),
    )

    for capability_id, name, description, domains in definitions:
        if capability_id not in existing:
            registry.register(
                Capability(
                    capability_id=capability_id,
                    name=name,
                    description=description,
                    domains=domains,
                )
            )


def _ensure_extended_skills(
    capability_registry: CapabilityRegistry,
    registry: SkillRegistry,
) -> None:
    """Add one or more valid skills for every extended capability."""

    existing = {item.skill_id for item in registry.list_all()}

    skill_map = {
        "customer_success": ("customer_success:retention_planning", "Customer Retention Planning"),
        "communications": ("communications:channel_coordination", "Channel Coordination"),
        "finance": ("finance:financial_analysis", "Financial Analysis"),
        "accounting_tax": ("accounting_tax:tax_review", "Tax Review"),
        "legal": ("legal:legal_research", "Legal Research"),
        "compliance": ("compliance:evidence_review", "Compliance Evidence Review"),
        "cybersecurity": ("cybersecurity:security_analysis", "Security Analysis"),
        "risk_fraud": ("risk_fraud:fraud_analysis", "Fraud Analysis"),
        "intelligence": ("intelligence:research_analysis", "Research Analysis"),
        "data_analytics": ("data_analytics:data_analysis", "Data Analysis"),
        "technology": ("technology:systems_analysis", "Systems Analysis"),
        "property_construction": ("property_construction:project_analysis", "Project Analysis"),
        "public_services": ("public_services:case_coordination", "Case Coordination"),
        "physical_systems": ("physical_systems:mission_planning", "Physical Systems Planning"),
        "strategy": ("strategy:strategic_analysis", "Strategic Analysis"),
    }

    descriptions = {
        "customer_success": "Plan controlled customer success and retention workflows.",
        "communications": "Coordinate communications across approved channels.",
        "finance": "Analyse financial performance and operating information.",
        "accounting_tax": "Review accounting and tax information against defined requirements.",
        "legal": "Conduct structured legal research using approved information.",
        "compliance": "Review compliance evidence against defined controls.",
        "cybersecurity": "Analyse security events, controls, and operational exposure.",
        "risk_fraud": "Analyse risk indicators and potential fraud patterns.",
        "intelligence": "Produce structured research and intelligence assessments.",
        "data_analytics": "Analyse business data and identify measurable patterns.",
        "technology": "Analyse systems, architecture, and technology workflows.",
        "property_construction": "Analyse property and construction project information.",
        "public_services": "Coordinate structured public-service cases and evidence.",
        "physical_systems": "Plan controlled physical-world operational workflows.",
        "strategy": "Analyse strategic options and business performance.",
    }

    for capability_id, (skill_id, name) in skill_map.items():
        if skill_id not in existing:
            capability_registry.get(capability_id)
            registry.register(
                Skill(
                    skill_id=skill_id,
                    name=name,
                    description=descriptions[capability_id],
                    capability_id=capability_id,
                )
            )


def build_mananze_workforce(
    capability_registry: CapabilityRegistry | None = None,
    skill_registry: SkillRegistry | None = None,
) -> tuple[WorkforceRegistry, tuple[WorkforceRole, ...]]:
    """Build and validate the canonical 200-role Mananze workforce."""

    capabilities = capability_registry or default_capability_registry()
    skills = skill_registry or default_skill_registry()

    _ensure_extended_capabilities(capabilities)
    _ensure_extended_skills(capabilities, skills)

    validator = WorkforceRoleValidator(capabilities, skills)
    registry = WorkforceRegistry()
    roles: list[WorkforceRole] = []

    for index, (domain_id, domain_name, capability_id) in enumerate(
        DOMAIN_DEFINITIONS,
        start=1,
    ):
        capability_skill_ids = tuple(
            skill.skill_id
            for skill in skills.list_all()
            if skill.capability_id == capability_id
        )

        if not capability_skill_ids:
            raise RuntimeError(
                f"canonical workforce capability has no registered skills: "
                f"{capability_id}"
            )

        orchestrator = WorkforceRole(
            role_id=f"orchestrator:{domain_id}",
            name=ORCHESTRATOR_NAMES[index - 1],
            description=f"Domain Orchestrator for {domain_name}.",
            capability_ids=(capability_id,),
            skill_ids=capability_skill_ids,
        )
        validator.validate(orchestrator)
        registry.register(orchestrator)
        roles.append(orchestrator)

        for specialist_index in range(1, 10):
            specialist_name = (
                f"{SPECIALIST_NAME_SEEDS[specialist_index - 1]} "
                f"{domain_name}"
            )
            specialist = WorkforceRole(
                role_id=f"specialist:{domain_id}:{specialist_index:02d}",
                name=specialist_name,
                description=(
                    f"Specialist Agent {specialist_index} for "
                    f"{domain_name}."
                ),
                capability_ids=(capability_id,),
                skill_ids=capability_skill_ids,
            )
            validator.validate(specialist)
            registry.register(specialist)
            roles.append(specialist)

    if len(roles) != 200:
        raise RuntimeError(
            f"canonical workforce must contain exactly 200 roles; got {len(roles)}"
        )

    if len({role.role_id for role in roles}) != 200:
        raise RuntimeError("canonical workforce contains duplicate role IDs")

    if len({role.name for role in roles}) != 200:
        raise RuntimeError("canonical workforce contains duplicate role names")

    return registry, tuple(roles)


def default_workforce_registry() -> WorkforceRegistry:
    """Return a validated registry containing exactly 200 workforce roles."""

    registry, _ = build_mananze_workforce()
    return registry


__all__ = [
    "DOMAIN_DEFINITIONS",
    "build_mananze_workforce",
    "default_workforce_registry",
]

