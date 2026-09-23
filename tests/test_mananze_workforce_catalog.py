from mananze_os.mananze_workforce_catalog import (
    DOMAIN_DEFINITIONS,
    build_mananze_workforce,
)


def test_canonical_workforce_has_exactly_200_roles():
    registry, roles = build_mananze_workforce()

    assert len(roles) == 200
    assert len(registry.list_all()) == 200


def test_canonical_workforce_has_20_orchestrators_and_180_specialists():
    _, roles = build_mananze_workforce()

    orchestrators = [
        role for role in roles if role.role_id.startswith("orchestrator:")
    ]
    specialists = [
        role for role in roles if role.role_id.startswith("specialist:")
    ]

    assert len(orchestrators) == 20
    assert len(specialists) == 180


def test_canonical_workforce_has_unique_ids_and_names():
    _, roles = build_mananze_workforce()

    assert len({role.role_id for role in roles}) == 200
    assert len({role.name for role in roles}) == 200


def test_every_domain_has_one_orchestrator_and_nine_specialists():
    _, roles = build_mananze_workforce()

    for domain_id, _, _ in DOMAIN_DEFINITIONS:
        matching = [
            role
            for role in roles
            if f":{domain_id}" in role.role_id
        ]

        assert len(matching) == 10
        assert sum(
            role.role_id.startswith("orchestrator:")
            for role in matching
        ) == 1
        assert sum(
            role.role_id.startswith("specialist:")
            for role in matching
        ) == 9


def test_workforce_roles_have_no_execution_authority():
    _, roles = build_mananze_workforce()

    for role in roles:
        assert not hasattr(role, "can_execute")
        assert not hasattr(role, "authority")
        assert not hasattr(role, "approval_power")
