"""Business-context capability discovery for Mananze Hub.

This layer identifies potentially relevant Hub capabilities from structured
observations. It does not execute, approve, authorize, or route actions.

Final execution decisions remain under Mananze OS.
"""
from __future__ import annotations

from dataclasses import dataclass

from mananze_hub.catalog import HubCapability, list_capabilities
from mananze_platform.intake import BusinessObservation


@dataclass(frozen=True)
class CapabilityCandidate:
    capability: HubCapability
    matched_observations: tuple[str, ...]


_KEYWORDS: dict[str, tuple[str, ...]] = {
    "mananze:marketing": (
        "marketing",
        "advertising",
        "social media",
        "content",
        "brand",
        "customers",
    ),
    "mananze:sales": (
        "sales",
        "lead",
        "leads",
        "pipeline",
        "customer",
        "conversion",
    ),
    "mananze:revenue": (
        "revenue",
        "income",
        "pricing",
        "profit",
        "sales",
    ),
    "mananze:finance": (
        "finance",
        "financial",
        "invoice",
        "invoices",
        "expense",
        "expenses",
        "accounting",
    ),
    "mananze:cybersecurity": (
        "cybersecurity",
        "security",
        "hack",
        "breach",
        "password",
        "phishing",
    ),
    "mananze:legal": (
        "legal",
        "contract",
        "compliance",
        "regulation",
        "policy",
    ),
    "mananze:data_analytics": (
        "data",
        "analytics",
        "report",
        "reports",
        "spreadsheet",
        "dashboard",
    ),
    "mananze:customer_service": (
        "support",
        "customer service",
        "complaints",
        "calls",
        "whatsapp",
        "queries",
    ),
    "mananze:logistics": (
        "logistics",
        "delivery",
        "deliveries",
        "fleet",
        "transport",
        "warehouse",
        "stock",
    ),
    "mananze:property": (
        "property",
        "properties",
        "real estate",
        "rent",
        "rental",
    ),
    "mananze:construction": (
        "construction",
        "building",
        "contractor",
        "site",
        "project",
    ),
    "mananze:crypto_web3": (
        "crypto",
        "cryptocurrency",
        "blockchain",
        "web3",
        "token",
        "wallet",
    ),
}


def discover_capabilities(
    observations: tuple[BusinessObservation, ...],
) -> tuple[CapabilityCandidate, ...]:
    """Return potentially relevant capabilities.

    Discovery is intentionally non-authoritative. A match means only that a
    capability may be relevant and should be considered by the OS.
    """
    candidates: list[CapabilityCandidate] = []

    for capability in list_capabilities():
        keywords = _KEYWORDS.get(capability.capability_id, ())
        matches: list[str] = []

        for observation in observations:
            text = observation.statement.casefold()
            if any(keyword in text for keyword in keywords):
                matches.append(observation.statement)

        if matches:
            candidates.append(
                CapabilityCandidate(
                    capability=capability,
                    matched_observations=tuple(matches),
                )
            )

    return tuple(candidates)


def resolve_os_capability_candidates(
    candidates: tuple[CapabilityCandidate, ...],
) -> tuple[str, ...]:
    """Translate Hub candidates into declared OS capability IDs.

    This function is a translation boundary only. It does not decide whether
    an OS capability is valid or executable. The OS compiler and capability
    registry remain authoritative.
    """
    resolved: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        for capability_id in candidate.capability.os_capability_ids:
            if capability_id not in seen:
                seen.add(capability_id)
                resolved.append(capability_id)

    return tuple(resolved)
