from mananze_os.business_twin import BusinessTwinBuilder
from mananze_os.business_truth import BusinessTruth
from mananze_os.capability_activation import CapabilityActivationEngine
from mananze_os.intelligence_fabric import IntelligenceObservation


def _truth(
    tenant_id: str,
    truth_id: str,
    subject: str,
    value,
) -> BusinessTruth:
    observation = IntelligenceObservation(
        observation_id=f"obs-{truth_id}",
        tenant_id=tenant_id,
        domain="business",
        kind="fact",
        subject=subject,
        value=value,
        confidence=1.0,
        source_reference=f"document:{truth_id}",
    )

    return BusinessTruth(
        truth_id=truth_id,
        tenant_id=tenant_id,
        subject=subject,
        value=value,
        status="established",
        confidence=1.0,
        source_type="business_document",
        source_reference=f"document:{truth_id}",
        observation_ids=(observation.observation_id,),
        effective_at=None,
    )


def _twin(tenant_id: str = "tenant-a", include_operations_evidence: bool = True):
    truths = [
        _truth(
            tenant_id,
            "truth-services",
            "services",
            ["security guarding"],
        ),
    ]

    if include_operations_evidence:
        truths.extend(
            [
                _truth(
                    tenant_id,
                    "truth-processes",
                    "processes",
                    ["quotation"],
                ),
                _truth(
                    tenant_id,
                    "truth-systems",
                    "systems",
                    ["WhatsApp"],
                ),
            ]
        )

    return BusinessTwinBuilder().build(
        tenant_id=tenant_id,
        truths=tuple(truths),
    )


def test_supported_capability_becomes_active():
    twin = _twin()

    plan = CapabilityActivationEngine().activate(
        twin,
        ("operations", "sales"),
    )

    assert plan.active_capability_ids == (
        "operations",
        "sales",
    )


def test_unsupported_capability_is_unavailable():
    twin = _twin(include_operations_evidence=False)

    plan = CapabilityActivationEngine().activate(
        twin,
        ("payment_collection",),
    )

    assert plan.unavailable_capability_ids == ("payment_collection",)


def test_twin_status_can_make_activation_conditional():
    twin = _twin()

    stale_twin = twin.__class__(
        **{
            **twin.__dict__,
            "status": "stale",
        }
    )

    plan = CapabilityActivationEngine().activate(
        stale_twin,
        ("operations",),
    )

    assert plan.conditional_capability_ids == ("operations",)


def test_activation_preserves_supporting_truth_observations():
    twin = _twin()

    plan = CapabilityActivationEngine().activate(
        twin,
        ("operations",),
    )

    activation = plan.activations[0]

    assert activation.supporting_truth_ids == (
        "obs-truth-processes",
        "obs-truth-services",
        "obs-truth-systems",
    )


def test_duplicate_candidates_are_deduplicated():
    twin = _twin()

    plan = CapabilityActivationEngine().activate(
        twin,
        ("operations", "operations", "sales"),
    )

    assert tuple(
        activation.capability_id
        for activation in plan.activations
    ) == ("operations", "sales")


def test_unknown_capability_is_rejected_by_existing_registry():
    twin = _twin()

    try:
        CapabilityActivationEngine().activate(
            twin,
            ("does_not_exist",),
        )
    except KeyError as exc:
        assert "unknown capability" in str(exc)
    else:
        raise AssertionError("unknown capability was accepted")


def test_active_capabilities_compile_through_existing_compiler():
    twin = _twin()

    engine = CapabilityActivationEngine()

    plan = engine.activate(
        twin,
        ("operations", "sales"),
    )

    requirements = engine.compile_active_requirements(
        twin=twin,
        work_order_id="wo-capability-activation",
        objective="operate and sell",
        plan=plan,
    )

    assert tuple(
        requirement.capability_id
        for requirement in requirements
    ) == ("operations", "sales")


def test_compilation_rejects_activation_from_another_tenant():
    twin = _twin("tenant-a")
    other_twin = _twin("tenant-b")

    engine = CapabilityActivationEngine()

    plan = engine.activate(
        twin,
        ("operations",),
    )

    try:
        engine.compile_active_requirements(
            twin=other_twin,
            work_order_id="wo-cross-tenant",
            objective="operate",
            plan=plan,
        )
    except PermissionError as exc:
        assert "tenant mismatch" in str(exc)
    else:
        raise AssertionError("cross-tenant activation was accepted")

