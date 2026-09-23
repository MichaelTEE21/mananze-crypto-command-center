from __future__ import annotations

from mananze_os.intelligence_fabric import IntelligenceObservation
from mananze_os.intelligence_provider import IntelligenceProvider
from mananze_os.obligation_registry import ObligationRegistry


class ObligationIntelligenceProvider(IntelligenceProvider):
    """Expose authoritative obligations as normalized OS intelligence."""

    provider_id = "mananze:obligations"
    domains = ("obligations", "economic")

    def __init__(self, registry: ObligationRegistry) -> None:
        self.registry = registry

    def observe(
        self,
        *,
        tenant_id: str,
        context: object | None = None,
    ) -> tuple[IntelligenceObservation, ...]:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        observations: list[IntelligenceObservation] = []

        for obligation in self.registry.list_for_tenant(tenant_id):
            observations.append(
                IntelligenceObservation(
                    observation_id=f"obligation:{obligation.obligation_id}",
                    tenant_id=obligation.tenant_id,
                    domain="obligations",
                    kind="fact",
                    subject=obligation.name,
                    value={
                        "obligation_id": obligation.obligation_id,
                        "obligation_type": obligation.obligation_type,
                        "counterparty": obligation.counterparty,
                        "amount": obligation.amount,
                        "currency": obligation.currency,
                        "frequency": obligation.frequency,
                        "due_date": obligation.due_date,
                        "renewal_date": obligation.renewal_date,
                        "status": obligation.status,
                        "approval_required": obligation.approval_required,
                    },
                    status="verified",
                    confidence=1.0,
                    source_reference=obligation.source_reference,
                )
            )

        return tuple(observations)


__all__ = ["ObligationIntelligenceProvider"]
