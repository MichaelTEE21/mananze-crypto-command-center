from mananze_os.compiler import IntelligenceCompiler
from mananze_os.intelligence_fabric import IntelligenceObservation
from mananze_os.work_order import WorkOrder


def test_intelligence_observation_does_not_change_compiled_requirements() -> None:
    compiler = IntelligenceCompiler()

    work_order = WorkOrder(
        work_order_id="wo-intelligence-boundary",
        tenant_id="tenant-a",
        objective="business operations report",
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:tenant-a:001",
        tenant_id="tenant-a",
        domain="business",
        kind="recommendation",
        subject="recommended_capability",
        value={"capability_id": "sales"},
        confidence=1.0,
        source_reference="intelligence:test",
    )

    compiled = compiler.compile(work_order)

    capability_ids = tuple(
        requirement.capability_id
        for requirement in compiled.requirements
    )

    assert intelligence.value["capability_id"] == "sales"
    assert capability_ids == ("operations", "reporting")
    assert "sales" not in capability_ids


def test_intelligence_observation_cannot_create_an_unknown_capability() -> None:
    compiler = IntelligenceCompiler()

    work_order = WorkOrder(
        work_order_id="wo-intelligence-unknown",
        tenant_id="tenant-a",
        objective="business operations report",
    )

    intelligence = IntelligenceObservation(
        observation_id="intel:tenant-a:002",
        tenant_id="tenant-a",
        domain="business",
        kind="recommendation",
        subject="recommended_capability",
        value={"capability_id": "execute_bank_transfer"},
        confidence=1.0,
        source_reference="intelligence:test",
    )

    compiled = compiler.compile(work_order)

    capability_ids = tuple(
        requirement.capability_id
        for requirement in compiled.requirements
    )

    assert intelligence.value["capability_id"] == "execute_bank_transfer"
    assert "execute_bank_transfer" not in capability_ids
