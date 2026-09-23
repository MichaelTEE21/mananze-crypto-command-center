from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


OrganizationType = Literal["technology_company"]
OwnershipType = Literal["trust"]
AgentStatus = Literal["active", "inactive", "retired"]


@dataclass(frozen=True)
class OwnershipIdentity:
    ownership_type: OwnershipType
    legal_name: str

    def __post_init__(self) -> None:
        if not self.legal_name.strip():
            raise ValueError("legal_name must not be blank")


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    name: str
    role: str
    domain: str
    capabilities: tuple[str, ...] = ()
    autonomy_level: int = 0
    version: str = "1.0.0"
    status: AgentStatus = "active"

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise ValueError("agent_id must not be blank")
        if not self.name.strip():
            raise ValueError("agent name must not be blank")
        if not self.role.strip():
            raise ValueError("agent role must not be blank")
        if not self.domain.strip():
            raise ValueError("agent domain must not be blank")
        if not 0 <= self.autonomy_level <= 4:
            raise ValueError("autonomy_level must be between 0 and 4")


@dataclass(frozen=True)
class OrganizationIdentity:
    name: str
    organization_type: OrganizationType
    powered_by: str
    ownership: OwnershipIdentity


class AgentRegistry:
    """Canonical identity registry for the Mananze AI workforce."""

    def __init__(
        self,
        organization: OrganizationIdentity,
        agents: tuple[AgentIdentity, ...] = (),
    ) -> None:
        self.organization = organization
        self._agents: dict[str, AgentIdentity] = {}

        for agent in agents:
            self.register(agent)

    def register(self, agent: AgentIdentity) -> AgentIdentity:
        existing = self._agents.get(agent.agent_id)

        if existing is not None and existing != agent:
            raise ValueError(
                f"agent_id already registered: {agent.agent_id}"
            )

        self._agents[agent.agent_id] = agent
        return agent

    def get(self, agent_id: str) -> AgentIdentity | None:
        return self._agents.get(agent_id)

    def list_all(self) -> tuple[AgentIdentity, ...]:
        return tuple(
            sorted(
                self._agents.values(),
                key=lambda agent: agent.agent_id,
            )
        )


def build_mananze_identity(trust_legal_name: str) -> OrganizationIdentity:
    """Build the canonical Mananze identity from the actual legal trust name."""

    return OrganizationIdentity(
        name="Mananze",
        organization_type="technology_company",
        powered_by="Artificial Intelligence",
        ownership=OwnershipIdentity(
            ownership_type="trust",
            legal_name=trust_legal_name,
        ),
    )


DEFAULT_AGENT_IDENTITIES = (
    AgentIdentity(
        agent_id="agent:sentinel",
        name="Sentinel",
        role="Security and threat intelligence",
        domain="cybersecurity",
        capabilities=("threat_detection", "security_analysis"),
    ),
    AgentIdentity(
        agent_id="agent:oracle",
        name="Oracle",
        role="Research and decision intelligence",
        domain="intelligence",
        capabilities=("research", "analysis", "decision_support"),
    ),
    AgentIdentity(
        agent_id="agent:fortune",
        name="Fortune",
        role="Economic and revenue intelligence",
        domain="economics",
        capabilities=("economic_analysis", "revenue_analysis"),
    ),
    AgentIdentity(
        agent_id="agent:astra",
        name="Astra",
        role="Legal intelligence",
        domain="legal",
        capabilities=("legal_research", "document_analysis"),
    ),
    AgentIdentity(
        agent_id="agent:atlas",
        name="Atlas",
        role="Operations and logistics intelligence",
        domain="operations",
        capabilities=("operations_planning", "logistics"),
    ),
)


__all__ = [
    "AgentIdentity",
    "AgentRegistry",
    "DEFAULT_AGENT_IDENTITIES",
    "OrganizationIdentity",
    "OwnershipIdentity",
    "build_mananze_identity",
]
