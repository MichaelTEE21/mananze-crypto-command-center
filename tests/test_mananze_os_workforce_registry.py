import pytest

from mananze_os.workforce_registry import WorkforceRegistry
from mananze_os.workforce_role import WorkforceRole


def make_role(role_id: str = "sales.specialist") -> WorkforceRole:
    return WorkforceRole(
        role_id=role_id,
        name="Sales Specialist",
        description="Convert qualified opportunities into customers.",
        capability_ids=("sales",),
        skill_ids=("sales:lead_qualification",),
    )


def test_workforce_registry_can_register_and_get_role() -> None:
    registry = WorkforceRegistry()
    role = make_role()

    registry.register(role)

    assert registry.get("sales.specialist") == role


def test_workforce_registry_lists_registered_roles() -> None:
    registry = WorkforceRegistry()
    role_one = make_role("sales.specialist")
    role_two = make_role("marketing.specialist")

    registry.register(role_one)
    registry.register(role_two)

    assert registry.list_all() == (role_one, role_two)


def test_workforce_registry_rejects_duplicate_role() -> None:
    registry = WorkforceRegistry()
    role = make_role()

    registry.register(role)

    with pytest.raises(
        ValueError,
        match="workforce role already registered: sales.specialist",
    ):
        registry.register(role)


def test_workforce_registry_rejects_unknown_role() -> None:
    registry = WorkforceRegistry()

    with pytest.raises(
        KeyError,
        match="unknown workforce role: missing.role",
    ):
        registry.get("missing.role")
