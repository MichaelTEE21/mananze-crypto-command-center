import pytest

from mananze_os.requirement import Requirement


def make_requirement(**overrides):
    values = {
        "requirement_id": "REQ-001",
        "tenant_id": "tenant-a",
        "product_or_material": "16mm white melamine board",
        "dimensions": "2750 x 1830 mm",
        "quantity": 2,
        "specification": "Cabinet panels",
        "edging": "1mm PVC",
        "backer": "3mm white board",
        "finish": "Matt",
        "evidence_ids": ("EVID-001",),
        "confirmation_status": "unconfirmed",
    }
    values.update(overrides)
    return Requirement(**values)


def test_valid_requirement_is_created():
    requirement = make_requirement()

    assert requirement.requirement_id == "REQ-001"
    assert requirement.tenant_id == "tenant-a"
    assert requirement.product_or_material == "16mm white melamine board"
    assert requirement.quantity == 2
    assert requirement.evidence_ids == ("EVID-001",)


def test_requirement_is_immutable():
    requirement = make_requirement()

    with pytest.raises((AttributeError, TypeError)):
        requirement.quantity = 5


def test_blank_requirement_id_is_rejected():
    with pytest.raises(ValueError, match="requirement_id is required"):
        make_requirement(requirement_id=" ")


def test_blank_tenant_id_is_rejected():
    with pytest.raises(ValueError, match="tenant_id is required"):
        make_requirement(tenant_id=" ")


def test_blank_product_or_material_is_rejected():
    with pytest.raises(ValueError, match="product_or_material is required"):
        make_requirement(product_or_material=" ")


def test_non_positive_quantity_is_rejected():
    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        make_requirement(quantity=0)

    with pytest.raises(ValueError, match="quantity must be greater than zero"):
        make_requirement(quantity=-1)


def test_blank_evidence_id_is_rejected():
    with pytest.raises(ValueError, match="evidence_ids cannot contain blank values"):
        make_requirement(evidence_ids=("EVID-001", " "))


def test_confirmation_status_is_required():
    with pytest.raises(ValueError, match="confirmation_status is required"):
        make_requirement(confirmation_status="")


def test_requirement_can_exist_without_optional_details():
    requirement = Requirement(
        requirement_id="REQ-002",
        tenant_id="tenant-a",
        product_or_material="Consulting service",
    )

    assert requirement.quantity == 1
    assert requirement.dimensions == ""
    assert requirement.evidence_ids == ()
    assert requirement.confirmation_status == "unconfirmed"

def test_invalid_confirmation_status_is_rejected():
    with pytest.raises(ValueError, match="invalid confirmation_status"):
        make_requirement(confirmation_status="unknown_status")
