"""Mananze OS Quality Controller Intelligence foundation."""

from dataclasses import dataclass
from typing import Literal

from mananze_os.workforce_planner import DynamicWorkforcePlan
from mananze_os.skill_registry import SkillRegistry, default_skill_registry


QualityDisposition = Literal[
    "pass",
    "fail",
    "review_required",
    "conflict",
    "insufficient_evidence",
]


@dataclass(frozen=True)
class QualityFinding:
    check_id: str
    category: str
    disposition: QualityDisposition
    message: str

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise ValueError("quality finding check ID is required")

        if not self.category.strip():
            raise ValueError("quality finding category is required")

        if not self.message.strip():
            raise ValueError("quality finding message is required")


@dataclass(frozen=True)
class QualityAssessment:
    assessment_id: str
    tenant_id: str
    work_order_id: str
    findings: tuple[QualityFinding, ...]

    @property
    def passed(self) -> bool:
        return all(
            finding.disposition == "pass"
            for finding in self.findings
        )

    @property
    def requires_review(self) -> bool:
        return any(
            finding.disposition
            in {
                "review_required",
                "conflict",
                "insufficient_evidence",
            }
            for finding in self.findings
        )

    @property
    def failed(self) -> bool:
        return any(
            finding.disposition == "fail"
            for finding in self.findings
        )


class QualityControllerIntelligence:
    """Cross-domain quality assessment contract.

    QCI evaluates quality signals but does not grant authority,
    permissions, approvals, or execution rights.
    """

    def assess(
        self,
        assessment_id: str,
        tenant_id: str,
        work_order_id: str,
        findings: tuple[QualityFinding, ...],
    ) -> QualityAssessment:
        if not assessment_id.strip():
            raise ValueError("assessment ID is required")

        if not tenant_id.strip():
            raise ValueError("tenant ID is required")

        if not work_order_id.strip():
            raise ValueError("work order ID is required")

        return QualityAssessment(
            assessment_id=assessment_id,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            findings=findings,
        )

    def assess_workforce_plan(
        self,
        assessment_id: str,
        tenant_id: str,
        workforce: DynamicWorkforcePlan,
        skill_registry: SkillRegistry | None = None,
    ) -> QualityAssessment:
        """Assess universal quality conditions of a planned workforce.

        QCI observes and reports quality. It does not authorize,
        approve, execute, or modify the workforce plan.
        """

        if not assessment_id.strip():
            raise ValueError("assessment ID is required")

        if not tenant_id.strip():
            raise ValueError("tenant ID is required")

        if not workforce.work_order_id.strip():
            raise ValueError("workforce work order ID is required")

        registry = skill_registry or default_skill_registry()

        findings: list[QualityFinding] = []

        findings.append(
            QualityFinding(
                check_id="workforce:work_order_identity",
                category="workforce_identity",
                disposition=(
                    "pass"
                    if workforce.work_order_id.strip()
                    else "fail"
                ),
                message="workforce work order identity is present",
            )
        )

        findings.append(
            QualityFinding(
                check_id="workforce:objective",
                category="workforce_completeness",
                disposition=(
                    "pass"
                    if workforce.objective.strip()
                    else "fail"
                ),
                message=(
                    "workforce objective is present"
                    if workforce.objective.strip()
                    else "workforce objective is missing"
                ),
            )
        )

        findings.append(
            QualityFinding(
                check_id="workforce:roles_present",
                category="workforce_completeness",
                disposition=(
                    "pass"
                    if workforce.roles
                    else "fail"
                ),
                message=(
                    "workforce contains planned roles"
                    if workforce.roles
                    else "workforce contains no planned roles"
                ),
            )
        )

        role_ids = [role.role_id for role in workforce.roles]
        capability_ids = [
            role.capability_id
            for role in workforce.roles
        ]

        duplicate_role_ids = {
            role_id
            for role_id in role_ids
            if role_ids.count(role_id) > 1
        }

        findings.append(
            QualityFinding(
                check_id="workforce:unique_roles",
                category="workforce_consistency",
                disposition=(
                    "pass"
                    if not duplicate_role_ids
                    else "fail"
                ),
                message=(
                    "workforce role identifiers are unique"
                    if not duplicate_role_ids
                    else (
                        "duplicate workforce role identifiers: "
                        + ", ".join(sorted(duplicate_role_ids))
                    )
                ),
            )
        )

        duplicate_capability_ids = {
            capability_id
            for capability_id in capability_ids
            if capability_ids.count(capability_id) > 1
        }

        findings.append(
            QualityFinding(
                check_id="workforce:unique_capabilities",
                category="workforce_consistency",
                disposition=(
                    "pass"
                    if not duplicate_capability_ids
                    else "fail"
                ),
                message=(
                    "workforce capability identifiers are unique"
                    if not duplicate_capability_ids
                    else (
                        "duplicate workforce capability identifiers: "
                        + ", ".join(
                            sorted(duplicate_capability_ids)
                        )
                    )
                ),
            )
        )

        missing_role_ids = [
            role.role_id
            for role in workforce.roles
            if not role.role_id.strip()
        ]

        findings.append(
            QualityFinding(
                check_id="workforce:role_identity",
                category="workforce_identity",
                disposition=(
                    "pass"
                    if not missing_role_ids
                    else "fail"
                ),
                message=(
                    "all workforce roles have identifiers"
                    if not missing_role_ids
                    else "one or more workforce roles have no role ID"
                ),
            )
        )

        missing_capability_ids = [
            role.role_id or "<unknown-role>"
            for role in workforce.roles
            if not role.capability_id.strip()
        ]

        findings.append(
            QualityFinding(
                check_id="workforce:capability_identity",
                category="workforce_identity",
                disposition=(
                    "pass"
                    if not missing_capability_ids
                    else "fail"
                ),
                message=(
                    "all workforce roles have capability identifiers"
                    if not missing_capability_ids
                    else (
                        "workforce roles missing capability identifiers: "
                        + ", ".join(sorted(missing_capability_ids))
                    )
                ),
            )
        )

        invalid_skill_references: list[str] = []

        for role in workforce.roles:
            for skill_id in role.skill_ids:
                try:
                    skill = registry.get(skill_id)
                except KeyError:
                    invalid_skill_references.append(skill_id)
                    continue

                if skill.capability_id != role.capability_id:
                    invalid_skill_references.append(
                        f"{skill_id}!=capability:{role.capability_id}"
                    )

        findings.append(
            QualityFinding(
                check_id="workforce:skill_references",
                category="workforce_consistency",
                disposition=(
                    "pass"
                    if not invalid_skill_references
                    else "fail"
                ),
                message=(
                    "all workforce skill references are valid"
                    if not invalid_skill_references
                    else (
                        "invalid workforce skill references: "
                        + ", ".join(
                            sorted(invalid_skill_references)
                        )
                    )
                ),
            )
        )

        invalid_role_objectives = [
            role.role_id or "<unknown-role>"
            for role in workforce.roles
            if not role.objective.strip()
        ]

        findings.append(
            QualityFinding(
                check_id="workforce:role_objectives",
                category="workforce_completeness",
                disposition=(
                    "pass"
                    if not invalid_role_objectives
                    else "fail"
                ),
                message=(
                    "all workforce roles have objectives"
                    if not invalid_role_objectives
                    else (
                        "workforce roles missing objectives: "
                        + ", ".join(
                            sorted(invalid_role_objectives)
                        )
                    )
                ),
            )
        )

        return self.assess(
            assessment_id=assessment_id,
            tenant_id=tenant_id,
            work_order_id=workforce.work_order_id,
            findings=tuple(findings),
        )


__all__ = [
    "QualityAssessment",
    "QualityControllerIntelligence",
    "QualityDisposition",
    "QualityFinding",
]
