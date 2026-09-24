"""Mananze Hub capability catalog.

This module is deliberately declarative. It does not execute work, route
providers, approve actions, or replace Mananze OS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class HubCapability:
    capability_id: str
    name: str
    description: str
    status: str = "available"


CAPABILITIES: Final[tuple[HubCapability, ...]] = (
    HubCapability(
        "mananze:crypto_web3",
        "Crypto & Web3",
        "Crypto, blockchain and Web3 research capabilities.",
    ),
    HubCapability(
        "mananze:marketing",
        "Marketing",
        "Marketing analysis, planning and content capabilities.",
    ),
    HubCapability(
        "mananze:sales",
        "Sales",
        "Sales analysis, pipeline and customer-conversion capabilities.",
    ),
    HubCapability(
        "mananze:revenue",
        "Revenue",
        "Revenue analysis, opportunities and commercial optimisation.",
    ),
    HubCapability(
        "mananze:finance",
        "Finance",
        "Business finance analysis and financial-operational intelligence.",
    ),
    HubCapability(
        "mananze:cybersecurity",
        "Cybersecurity",
        "Cybersecurity assessment, monitoring and response capabilities.",
    ),
    HubCapability(
        "mananze:legal",
        "Legal",
        "Legal-information and business-compliance capabilities.",
    ),
    HubCapability(
        "mananze:data_analytics",
        "Data & Analytics",
        "Business data analysis and intelligence capabilities.",
    ),
    HubCapability(
        "mananze:customer_service",
        "Customer Service",
        "Customer communication and service-operation capabilities.",
    ),
    HubCapability(
        "mananze:logistics",
        "Logistics",
        "Logistics planning and operational capabilities.",
    ),
    HubCapability(
        "mananze:property",
        "Property",
        "Property and property-business capabilities.",
    ),
    HubCapability(
        "mananze:construction",
        "Construction",
        "Construction-business planning and operational capabilities.",
    ),
)


def list_capabilities() -> tuple[HubCapability, ...]:
    """Return the capabilities currently available to Mananze OS."""
    return CAPABILITIES


def get_capability(capability_id: str) -> HubCapability | None:
    """Return a capability by ID without executing anything."""
    return next(
        (capability for capability in CAPABILITIES if capability.capability_id == capability_id),
        None,
    )
