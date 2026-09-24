from mananze_os.diagnostic import (
    BusinessDiagnostic,
    DiagnosticFinding,
    DiagnosticReport,
    ImplementationScope,
)
from mananze_os.intelligence_fabric import IntelligenceObservation


def test_diagnostic_is_tenant_scoped() -> None:
    diagnostic = BusinessDiagnostic()

    observation = IntelligenceObservation(
        observation_id="intel:tenant-a:001",
        tenant_id="tenant-a",
        domain="sales",
        kind="gap",
        subject="lead follow-up",
        value="Leads are not followed up consistently.",
        confidence=0.95,
    )

    report = diagnostic.diagnose(
        tenant_id="tenant-a",
        business_objective="Improve sales conversion",
        observations=(observation,),
    )

    assert report.tenant_id == "tenant-a"
    assert report.observation_ids == ("intel:tenant-a:001",)
    assert report.findings[0].category == "sales"
    assert report.findings[0].severity == "high"


def test_diagnostic_rejects_cross_tenant_observations() -> None:
    diagnostic = BusinessDiagnostic()

    observation = IntelligenceObservation(
        observation_id="intel:tenant-b:001",
        tenant_id="tenant-b",
        domain="sales",
        kind="gap",
        subject="lead follow-up",
        value="Missing follow-up process.",
        confidence=1.0,
    )

    try:
        diagnostic.diagnose(
            tenant_id="tenant-a",
            business_objective="Improve sales",
            observations=(observation,),
        )
    except PermissionError as exc:
        assert "cross-tenant" in str(exc)
    else:
        raise AssertionError("expected cross-tenant access to be rejected")


def test_diagnostic_preserves_recommended_capabilities_as_advisory_scope() -> None:
    diagnostic = BusinessDiagnostic()

    observation = IntelligenceObservation(
        observation_id="intel:tenant-a:002",
        tenant_id="tenant-a",
        domain="sales",
        kind="recommendation",
        subject="recommended capability",
        value={"capability_id": "sales"},
        confidence=0.91,
    )

    report = diagnostic.diagnose(
        tenant_id="tenant-a",
        business_objective="Improve sales",
        observations=(observation,),
    )

    assert report.scope.recommended_capability_ids == ("sales",)
    assert report.findings[0].recommended_action == (
        "Evaluate capability 'sales'"
    )


def test_diagnostic_tracks_dependencies_and_integration_gaps() -> None:
    diagnostic = BusinessDiagnostic()

    observations = (
        IntelligenceObservation(
            observation_id="intel:tenant-a:003",
            tenant_id="tenant-a",
            domain="integration",
            kind="gap",
            subject="CRM integration",
            value="CRM data is not connected.",
            confidence=0.90,
        ),
        IntelligenceObservation(
            observation_id="intel:tenant-a:004",
            tenant_id="tenant-a",
            domain="operations",
            kind="dependency",
            subject="owner approval",
            value="Important actions require owner approval.",
            confidence=1.0,
        ),
    )

    report = diagnostic.diagnose(
        tenant_id="tenant-a",
        business_objective="Improve business operations",
        observations=observations,
    )

    assert report.scope.integration_requirements == (
        "CRM data is not connected.",
    )
    assert report.scope.dependencies == (
        "Important actions require owner approval.",
    )
    assert report.scope.estimated_complexity == "medium"


def test_diagnostic_report_exposes_high_priority_findings() -> None:
    finding = DiagnosticFinding(
        finding_id="finding-1",
        tenant_id="tenant-a",
        category="security",
        severity="critical",
        title="Security gap",
        description="Security control is missing.",
        confidence=0.99,
    )

    scope = ImplementationScope(
        tenant_id="tenant-a",
        objective="Improve security",
    )

    report = DiagnosticReport(
        report_id="report-1",
        tenant_id="tenant-a",
        business_objective="Improve security",
        findings=(finding,),
        scope=scope,
    )

    assert report.high_priority_findings == (finding,)


def test_empty_diagnostic_is_valid_and_low_complexity() -> None:
    report = BusinessDiagnostic().diagnose(
        tenant_id="tenant-a",
        business_objective="Understand business operations",
        observations=(),
    )

    assert report.findings == ()
    assert report.scope.estimated_complexity == "low"
    assert report.scope.recommended_capability_ids == ()
