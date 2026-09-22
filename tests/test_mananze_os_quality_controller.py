import pytest

from mananze_os.quality_controller import (
    QualityControllerIntelligence,
    QualityFinding,
)
from mananze_os.skill_registry import default_skill_registry
from mananze_os.workforce_planner import (
    DynamicWorkforcePlan,
    PlannedRole,
)


def make_workforce() -> DynamicWorkforcePlan:
    return DynamicWorkforcePlan(
        work_order_id="wo-qci-001",
        objective="Improve customer acquisition",
        roles=(
            PlannedRole(
                role_id="marketing",
                name="Marketing",
                objective="Plan targeted marketing activity.",
                capability_id="marketing",
                skill_ids=(
                    "marketing:campaign_planning",
                    "marketing:content_creation",
                ),
            ),
            PlannedRole(
                role_id="lead_generation",
                name="Lead Generation",
                objective="Identify qualified prospects.",
                capability_id="lead_generation",
                skill_ids=(
                    "lead_generation:prospecting",
                    "lead_generation:qualification",
                ),
            ),
        ),
    )


def test_qci_assesses_valid_workforce_plan():
    qci = QualityControllerIntelligence()

    assessment = qci.assess_workforce_plan(
        assessment_id="qci-001",
        tenant_id="tenant-001",
        workforce=make_workforce(),
    )

    assert assessment.passed is True
    assert assessment.failed is False
    assert assessment.requires_review is False
    assert len(assessment.findings) == 9


def test_qci_detects_empty_workforce():
    qci = QualityControllerIntelligence()

    workforce = DynamicWorkforcePlan(
        work_order_id="wo-qci-002",
        objective="Test empty workforce",
        roles=(),
    )

    assessment = qci.assess_workforce_plan(
        assessment_id="qci-002",
        tenant_id="tenant-001",
        workforce=workforce,
    )

    assert assessment.failed is True

    finding = next(
        item
        for item in assessment.findings
        if item.check_id == "workforce:roles_present"
    )

    assert finding.disposition == "fail"


def test_qci_detects_duplicate_roles_and_capabilities():
    qci = QualityControllerIntelligence()

    workforce = DynamicWorkforcePlan(
        work_order_id="wo-qci-003",
        objective="Test duplicates",
        roles=(
            PlannedRole(
                role_id="marketing",
                name="Marketing",
                objective="Marketing objective",
                capability_id="marketing",
            ),
            PlannedRole(
                role_id="marketing",
                name="Marketing Duplicate",
                objective="Marketing duplicate objective",
                capability_id="marketing",
            ),
        ),
    )

    assessment = qci.assess_workforce_plan(
        assessment_id="qci-003",
        tenant_id="tenant-001",
        workforce=workforce,
    )

    role_finding = next(
        item
        for item in assessment.findings
        if item.check_id == "workforce:unique_roles"
    )

    capability_finding = next(
        item
        for item in assessment.findings
        if item.check_id == "workforce:unique_capabilities"
    )

    assert role_finding.disposition == "fail"
    assert capability_finding.disposition == "fail"


def test_qci_detects_unknown_skill():
    qci = QualityControllerIntelligence()

    workforce = DynamicWorkforcePlan(
        work_order_id="wo-qci-004",
        objective="Test invalid skill",
        roles=(
            PlannedRole(
                role_id="marketing",
                name="Marketing",
                objective="Marketing objective",
                capability_id="marketing",
                skill_ids=("marketing:does_not_exist",),
            ),
        ),
    )

    assessment = qci.assess_workforce_plan(
        assessment_id="qci-004",
        tenant_id="tenant-001",
        workforce=workforce,
    )

    finding = next(
        item
        for item in assessment.findings
        if item.check_id == "workforce:skill_references"
    )

    assert finding.disposition == "fail"


def test_qci_detects_skill_capability_mismatch():
    qci = QualityControllerIntelligence()

    workforce = DynamicWorkforcePlan(
        work_order_id="wo-qci-005",
        objective="Test skill capability mismatch",
        roles=(
            PlannedRole(
                role_id="marketing",
                name="Marketing",
                objective="Marketing objective",
                capability_id="marketing",
                skill_ids=("sales:follow_up",),
            ),
        ),
    )

    assessment = qci.assess_workforce_plan(
        assessment_id="qci-005",
        tenant_id="tenant-001",
        workforce=workforce,
    )

    finding = next(
        item
        for item in assessment.findings
        if item.check_id == "workforce:skill_references"
    )

    assert finding.disposition == "fail"


def test_qci_detects_missing_role_objective():
    qci = QualityControllerIntelligence()

    workforce = DynamicWorkforcePlan(
        work_order_id="wo-qci-006",
        objective="Test missing role objective",
        roles=(
            PlannedRole(
                role_id="marketing",
                name="Marketing",
                objective="",
                capability_id="marketing",
            ),
        ),
    )

    assessment = qci.assess_workforce_plan(
        assessment_id="qci-006",
        tenant_id="tenant-001",
        workforce=workforce,
    )

    finding = next(
        item
        for item in assessment.findings
        if item.check_id == "workforce:role_objectives"
    )

    assert finding.disposition == "fail"


def test_qci_rejects_missing_identity():
    qci = QualityControllerIntelligence()

    with pytest.raises(ValueError):
        qci.assess_workforce_plan(
            assessment_id="",
            tenant_id="tenant-001",
            workforce=make_workforce(),
        )


def test_qci_preserves_manual_findings_contract():
    qci = QualityControllerIntelligence()

    finding = QualityFinding(
        check_id="evidence:test",
        category="evidence",
        disposition="insufficient_evidence",
        message="Evidence is incomplete.",
    )

    assessment = qci.assess(
        assessment_id="qci-008",
        tenant_id="tenant-001",
        work_order_id="wo-qci-008",
        findings=(finding,),
    )

    assert assessment.passed is False
    assert assessment.requires_review is True
    assert assessment.failed is False
