"""Mananze Hub capability catalog.

This module is deliberately declarative. It does not execute work, route
providers, approve actions, or replace Mananze OS.

Hub capabilities may declare the OS capability IDs they require, but the
Mananze OS capability registry remains authoritative and must validate every
declared capability before execution.
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
    os_capability_ids: tuple[str, ...] = ()


CAPABILITIES: Final[tuple[HubCapability, ...]] = (
    HubCapability(
        "mananze:crypto_web3",
        "Crypto & Web3",
        "Crypto, blockchain and Web3 research capabilities.",
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:marketing",
        "Marketing",
        "Marketing analysis, planning and content capabilities.",
        os_capability_ids=("marketing",),
    ),
    HubCapability(
        "mananze:sales",
        "Sales",
        "Sales analysis, pipeline and customer-conversion capabilities.",
        os_capability_ids=("sales",),
    ),
    HubCapability(
        "mananze:revenue",
        "Revenue",
        "Revenue analysis, opportunities and commercial optimisation.",
        os_capability_ids=("revenue",),
    ),
    HubCapability(
        "mananze:finance",
        "Finance",
        "Business finance analysis and financial-operational intelligence.",
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:cybersecurity",
        "Cybersecurity",
        "Cybersecurity assessment, monitoring and response capabilities.",
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:legal",
        "Legal",
        "Legal-information and business-compliance capabilities.",
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:data_analytics",
        "Data & Analytics",
        "Business data analysis and intelligence capabilities.",
        os_capability_ids=("reporting",),
    ),
    HubCapability(
        "mananze:customer_service",
        "Customer Service",
        "Customer communication and service-operation capabilities.",
        os_capability_ids=(
            "customer_communications",
            "retention",
            "reporting",
        ),
    ),
    HubCapability(
        "mananze:logistics",
        "Logistics",
        "Logistics planning and operational capabilities.",
        os_capability_ids=(
            "logistics",
            "fleet",
            "cost_analysis",
            "revenue",
            "reporting",
        ),
    ),
    HubCapability(
        "mananze:property",
        "Property",
        "Property and property-business capabilities.",
        os_capability_ids=(),
    ),
    HubCapability(
        "mananze:construction",
        "Construction",
        "Construction-business planning and operational capabilities.",
        os_capability_ids=("operations", "reporting"),
    ),
)


def list_capabilities() -> tuple[HubCapability, ...]:
    """Return the capabilities currently available to Mananze OS."""
    return CAPABILITIES


def get_capability(capability_id: str) -> HubCapability | None:
    """Return a capability by ID without executing anything."""
    return next(
        (
            capability
            for capability in CAPABILITIES
            if capability.capability_id == capability_id
        ),
        None,
    )
