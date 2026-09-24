import pytest

from mananze_hub.catalog import HubCapability
from mananze_hub.catalog_validation import (
    assert_valid_catalog,
    validate_catalog,
)
from mananze_os.capability_registry import default_capability_registry


def test_current_hub_catalog_is_valid_against_os_registry():
    errors = validate_catalog(
        os_registry=default_capability_registry(),
    )

    assert errors == ()


def test_unknown_dependency_is_reported():
    capability = HubCapability(
        capability_id="mananze:test",
        name="Test",
        description="Test capability",
        dependencies=("mananze:does_not_exist",),
    )

    errors = validate_catalog(
        capabilities=(capability,),
    )

    assert errors == (
        "mananze:test: unknown dependency: mananze:does_not_exist",
    )


def test_unknown_os_capability_is_reported():
    capability = HubCapability(
        capability_id="mananze:test",
        name="Test",
        description="Test capability",
        os_capability_ids=("does_not_exist",),
    )

    errors = validate_catalog(
        capabilities=(capability,),
        os_registry=default_capability_registry(),
    )

    assert errors == (
        "mananze:test: unknown OS capability: does_not_exist",
    )


def test_duplicate_capability_ids_are_reported():
    capability_a = HubCapability(
        capability_id="mananze:test",
        name="Test A",
        description="Test capability A",
    )
    capability_b = HubCapability(
        capability_id="mananze:test",
        name="Test B",
        description="Test capability B",
    )

    errors = validate_catalog(
        capabilities=(capability_a, capability_b),
    )

    assert errors == (
        "duplicate capability_id: mananze:test",
    )


def test_assert_valid_catalog_raises_for_invalid_catalog():
    capability = HubCapability(
        capability_id="mananze:test",
        name="Test",
        description="Test capability",
        dependencies=("mananze:missing",),
    )

    with pytest.raises(
        ValueError,
        match="invalid MANANZE HUB capability catalog",
    ):
        assert_valid_catalog(
            capabilities=(capability,),
        )
