"""Central registry for approved Mananze OS provider adapters."""

from .provider import Provider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    def register(self, provider: Provider) -> None:
        provider_id = provider.provider_id

        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id is required")

        if provider_id in self._providers:
            raise ValueError(f"provider already registered: {provider_id}")

        self._providers[provider_id] = provider

    def get(self, provider_id: str) -> Provider:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id is required")

        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(f"unknown provider: {provider_id}") from exc

    def list_all(self) -> tuple[Provider, ...]:
        return tuple(self._providers.values())


__all__ = ["ProviderRegistry"]
