from mananze_os.workforce_fabric import WorkforceFabric


def test_default_workforce_fabric_contains_200_roles() -> None:
    fabric = WorkforceFabric.with_default_workforce()

    roles = fabric.list_roles()

    assert len(roles) == 200


def test_default_workforce_fabric_contains_20_orchestrators() -> None:
    fabric = WorkforceFabric.with_default_workforce()

    assert sum(
        role.role_id.startswith("orchestrator:")
        for role in fabric.list_roles()
    ) == 20


def test_default_workforce_fabric_contains_180_specialists() -> None:
    fabric = WorkforceFabric.with_default_workforce()

    assert sum(
        role.role_id.startswith("specialist:")
        for role in fabric.list_roles()
    ) == 180


def test_default_workforce_can_retrieve_named_roles() -> None:
    fabric = WorkforceFabric.with_default_workforce()

    assert fabric.get_role("orchestrator:marketing").name == "Maven"
    assert fabric.get_role("orchestrator:cybersecurity").name == "Cipher"


def test_default_workforce_remains_assignable_through_existing_fabric() -> None:
    fabric = WorkforceFabric.with_default_workforce()

    role = fabric.get_role("specialist:marketing:01")

    assert role.capability_ids == ("marketing",)
