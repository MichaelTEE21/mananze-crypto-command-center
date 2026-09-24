from mananze_hub.catalog import (
    CAPABILITIES,
    HubCapability,
    get_capability,
    list_capabilities,
)


def test_catalog_preserves_existing_capability_ids():
    capability_ids = tuple(capability.capability_id for capability in list_capabilities())

    assert "mananze:crypto_web3" in capability_ids
    assert "mananze:marketing" in capability_ids
    assert "mananze:sales" in capability_ids
    assert "mananze:revenue" in capability_ids
    assert "mananze:finance" in capability_ids
    assert "mananze:cybersecurity" in capability_ids
    assert "mananze:legal" in capability_ids
    assert "mananze:data_analytics" in capability_ids
    assert "mananze:customer_service" in capability_ids
    assert "mananze:logistics" in capability_ids
    assert "mananze:property" in capability_ids
    assert "mananze:construction" in capability_ids


def test_catalog_capabilities_have_manifest_fields():
    for capability in CAPABILITIES:
        assert capability.capability_id.strip()
        assert capability.name.strip()
        assert capability.description.strip()
        assert capability.version.strip()
        assert capability.status in {
            "draft",
            "validated",
            "available",
            "deprecated",
        }
        assert capability.risk in {
            "low",
            "medium",
            "high",
            "critical",
        }


def test_catalog_capability_manifest_contains_unique_collections():
    for capability in CAPABILITIES:
        assert len(capability.inputs) == len(set(capability.inputs))
        assert len(capability.outputs) == len(set(capability.outputs))
        assert len(capability.dependencies) == len(set(capability.dependencies))
        assert len(capability.permissions) == len(set(capability.permissions))
        assert len(capability.supported_channels) == len(
            set(capability.supported_channels)
        )
        assert len(capability.evidence_requirements) == len(
            set(capability.evidence_requirements)
        )
        assert len(capability.os_capability_ids) == len(
            set(capability.os_capability_ids)
        )


def test_hub_capability_rejects_blank_required_fields():
    try:
        HubCapability(
            capability_id="",
            name="Test",
            description="Test capability",
        )
    except ValueError as exc:
        assert str(exc) == "capability_id is required"
    else:
        raise AssertionError("Expected ValueError")


def test_hub_capability_rejects_duplicate_manifest_values():
    try:
        HubCapability(
            capability_id="mananze:test",
            name="Test",
            description="Test capability",
            inputs=("business", "business"),
        )
    except ValueError as exc:
        assert str(exc) == "inputs cannot contain duplicates"
    else:
        raise AssertionError("Expected ValueError")


def test_get_capability_returns_manifest():
    capability = get_capability("mananze:logistics")

    assert capability is not None
    assert capability.version
    assert capability.inputs
    assert capability.outputs
    assert capability.permissions
    assert capability.evidence_requirements
    assert capability.os_capability_ids
