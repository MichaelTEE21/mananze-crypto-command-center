"""Mananze OS workforce skill registry foundation."""

from mananze_os.skill import Skill


class SkillRegistry:
    """Registry of skills available to the Mananze workforce."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        if not skill.skill_id.strip():
            raise ValueError("skill_id is required")

        if skill.skill_id in self._skills:
            raise ValueError(
                f"skill already registered: {skill.skill_id}"
            )

        self._skills[skill.skill_id] = skill

    def get(self, skill_id: str) -> Skill:
        try:
            return self._skills[skill_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown skill: {skill_id}"
            ) from exc

    def list_all(self) -> tuple[Skill, ...]:
        return tuple(self._skills.values())


def default_skill_registry() -> SkillRegistry:
    """Create the initial Mananze OS skill catalog."""

    registry = SkillRegistry()

    skills = (
        Skill(
            skill_id="marketing:campaign_planning",
            name="Campaign Planning",
            description="Plan targeted marketing campaigns against defined business objectives.",
            capability_id="marketing",
        ),
        Skill(
            skill_id="marketing:content_creation",
            name="Content Creation",
            description="Create controlled marketing content for approved campaigns and channels.",
            capability_id="marketing",
        ),
        Skill(
            skill_id="lead_generation:prospecting",
            name="Prospecting",
            description="Identify potential customers that match defined qualification criteria.",
            capability_id="lead_generation",
        ),
        Skill(
            skill_id="lead_generation:qualification",
            name="Lead Qualification",
            description="Evaluate prospects against defined qualification criteria.",
            capability_id="lead_generation",
        ),
        Skill(
            skill_id="sales:lead_qualification",
            name="Lead Qualification",
            description="Qualify sales opportunities before progression through the sales workflow.",
            capability_id="sales",
        ),
        Skill(
            skill_id="sales:follow_up",
            name="Sales Follow-up",
            description="Manage controlled follow-up with qualified sales opportunities.",
            capability_id="sales",
        ),
        Skill(
            skill_id="appointment_booking:scheduling",
            name="Appointment Scheduling",
            description="Coordinate customer appointments against approved availability.",
            capability_id="appointment_booking",
        ),
        Skill(
            skill_id="customer_communications:messaging",
            name="Customer Messaging",
            description="Manage controlled customer communications across approved channels.",
            capability_id="customer_communications",
        ),
        Skill(
            skill_id="retention:engagement",
            name="Customer Engagement",
            description="Coordinate activities intended to maintain customer engagement.",
            capability_id="retention",
        ),
        Skill(
            skill_id="revenue:performance_analysis",
            name="Revenue Performance Analysis",
            description="Analyse revenue performance and identify measurable opportunities.",
            capability_id="revenue",
        ),
        Skill(
            skill_id="operations:workflow_coordination",
            name="Workflow Coordination",
            description="Coordinate operational workflows against defined objectives and constraints.",
            capability_id="operations",
        ),
        Skill(
            skill_id="logistics:route_planning",
            name="Route Planning",
            description="Plan controlled movement of goods and services across logistics workflows.",
            capability_id="logistics",
        ),
        Skill(
            skill_id="fleet:fleet_monitoring",
            name="Fleet Monitoring",
            description="Monitor fleet activity, utilisation, and operational status.",
            capability_id="fleet",
        ),
        Skill(
            skill_id="cost_analysis:cost_review",
            name="Cost Review",
            description="Review operating costs and identify measurable cost drivers.",
            capability_id="cost_analysis",
        ),
        Skill(
            skill_id="reporting:business_reporting",
            name="Business Reporting",
            description="Produce evidence-based reports from approved business information.",
            capability_id="reporting",
        ),
    )

    for skill in skills:
        registry.register(skill)

    return registry


__all__ = [
    "Skill",
    "SkillRegistry",
    "default_skill_registry",
]
