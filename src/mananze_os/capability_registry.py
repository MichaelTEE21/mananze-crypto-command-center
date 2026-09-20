"""Mananze OS capability registry foundation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    capability_id: str
    name: str
    description: str
    domains: tuple[str, ...]


class CapabilityRegistry:
    """Registry of capabilities available to the Mananze workforce."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if not capability.capability_id.strip():
            raise ValueError("capability_id is required")

        if capability.capability_id in self._capabilities:
            raise ValueError(
                f"capability already registered: {capability.capability_id}"
            )

        self._capabilities[capability.capability_id] = capability

    def get(self, capability_id: str) -> Capability:
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown capability: {capability_id}"
            ) from exc

    def list_all(self) -> tuple[Capability, ...]:
        return tuple(self._capabilities.values())


def default_capability_registry() -> CapabilityRegistry:
    """Create the initial Mananze OS capability catalog."""

    registry = CapabilityRegistry()

    capabilities = (
        Capability(
            capability_id="marketing",
            name="Marketing",
            description="Generate and manage qualified demand.",
            domains=("business", "growth"),
        ),
        Capability(
            capability_id="lead_generation",
            name="Lead Generation",
            description="Identify and qualify potential customers.",
            domains=("business", "growth", "sales"),
        ),
        Capability(
            capability_id="sales",
            name="Sales",
            description="Convert qualified opportunities into customers.",
            domains=("business", "sales"),
        ),
        Capability(
            capability_id="appointment_booking",
            name="Appointment Booking",
            description="Convert customer interest into scheduled appointments.",
            domains=("business", "customer", "operations"),
        ),
        Capability(
            capability_id="customer_communications",
            name="Customer Communications",
            description="Manage controlled customer communications.",
            domains=("business", "customer", "communications"),
        ),
        Capability(
            capability_id="retention",
            name="Customer Retention",
            description="Improve repeat engagement and customer retention.",
            domains=("business", "customer", "growth"),
        ),
        Capability(
            capability_id="revenue",
            name="Revenue",
            description="Measure and improve revenue performance.",
            domains=("business", "finance", "growth"),
        ),
        Capability(
            capability_id="operations",
            name="Operations",
            description="Coordinate business operational workflows.",
            domains=("business", "operations"),
        ),
        Capability(
            capability_id="logistics",
            name="Logistics",
            description="Plan and coordinate movement of goods and services.",
            domains=("business", "operations", "logistics"),
        ),
        Capability(
            capability_id="fleet",
            name="Fleet Management",
            description="Manage vehicle and fleet operations.",
            domains=("business", "operations", "logistics"),
        ),
        Capability(
            capability_id="cost_analysis",
            name="Cost Analysis",
            description="Analyse operating costs and identify savings opportunities.",
            domains=("business", "finance", "operations"),
        ),
        Capability(
            capability_id="reporting",
            name="Reporting",
            description="Produce evidence-based operational and business reports.",
            domains=("business", "intelligence", "reporting"),
        ),
    )

    for capability in capabilities:
        registry.register(capability)

    return registry


__all__ = [
    "Capability",
    "CapabilityRegistry",
    "default_capability_registry",
]
