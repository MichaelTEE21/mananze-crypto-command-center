from __future__ import annotations

import pytest

from mananze_os.organization_identity import (
    AgentIdentity,
    AgentRegistry,
    DEFAULT_AGENT_IDENTITIES,
    build_mananze_identity,
)


def test_mananze_is_identified_as_ai_powered_technology_company():
    identity = build_mananze_identity("Mananze Family Trust")

    assert identity.name == "Mananze"
    assert identity.organization_type == "technology_company"
    assert identity.powered_by == "Artificial Intelligence"
    assert identity.ownership.ownership_type == "trust"
    assert identity.ownership.legal_name == "Mananze Family Trust"


def test_blank_trust_name_is_rejected():
    with pytest.raises(ValueError):
        build_mananze_identity("")


def test_agents_have_stable_named_identities():
    registry = AgentRegistry(
        build_mananze_identity("Mananze Family Trust"),
        DEFAULT_AGENT_IDENTITIES,
    )

    sentinel = registry.get("agent:sentinel")

    assert sentinel is not None
    assert sentinel.name == "Sentinel"
    assert sentinel.domain == "cybersecurity"


def test_agent_identity_is_separate_from_authority():
    agent = AgentIdentity(
        agent_id="agent:test",
        name="Test Agent",
        role="Testing",
        domain="quality",
        autonomy_level=0,
    )

    assert agent.autonomy_level == 0
    assert not hasattr(agent, "can_execute")


def test_duplicate_agent_id_cannot_change_identity():
    registry = AgentRegistry(
        build_mananze_identity("Mananze Family Trust")
    )

    registry.register(
        AgentIdentity(
            agent_id="agent:test",
            name="Test",
            role="Testing",
            domain="quality",
        )
    )

    with pytest.raises(ValueError):
        registry.register(
            AgentIdentity(
                agent_id="agent:test",
                name="Different Agent",
                role="Different role",
                domain="different",
            )
        )
