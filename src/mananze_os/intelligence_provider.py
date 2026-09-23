from __future__ import annotations

from typing import Protocol

from mananze_os.intelligence_fabric import (
    IntelligenceObservation,
)


class IntelligenceProvider(Protocol):
    """Contract implemented by intelligence-producing subsystems."""

    @property
    def provider_id(self) -> str:
        ...

    @property
    def domains(self) -> tuple[str, ...]:
        ...

    def observe(
        self,
        *,
        tenant_id: str,
        context: object | None = None,
    ) -> tuple[IntelligenceObservation, ...]:
        ...


class IntelligenceProviderRegistry:
    """Registry for governed intelligence-producing providers."""

    def __init__(self) -> None:
        self._providers: dict[str, IntelligenceProvider] = {}

    def register(self, provider: IntelligenceProvider) -> None:
        provider_id = provider.provider_id

        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id must be a non-empty string")

        if provider_id in self._providers:
            raise ValueError(
                f"intelligence provider already exists: {provider_id}"
            )

        self._providers[provider_id] = provider

    def get(self, provider_id: str) -> IntelligenceProvider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown intelligence provider: {provider_id}"
            ) from exc

    def list_all(self) -> tuple[IntelligenceProvider, ...]:
        return tuple(self._providers.values())

    def providers_for_domain(
        self,
        domain: str,
    ) -> tuple[IntelligenceProvider, ...]:
        return tuple(
            provider
            for provider in self._providers.values()
            if domain in provider.domains
        )


class IntelligenceCoordinator:
    """Coordinates providers and publishes their observations to the Fabric."""

    def __init__(
        self,
        fabric,
        registry: IntelligenceProviderRegistry,
    ) -> None:
        self.fabric = fabric
        self.registry = registry

    def collect(
        self,
        *,
        provider_id: str,
        tenant_id: str,
        context: object | None = None,
    ) -> tuple[IntelligenceObservation, ...]:
        provider = self.registry.get(provider_id)

        observations = provider.observe(
            tenant_id=tenant_id,
            context=context,
        )

        for observation in observations:
            if observation.tenant_id != tenant_id:
                raise PermissionError(
                    "intelligence provider returned cross-tenant observation"
                )

            self.fabric.publish(observation)

        return observations
