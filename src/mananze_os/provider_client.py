from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from .provider_transport import (
    ProviderRequest,
    ProviderResponse,
    ProviderTransport,
    ProviderTransportError,
)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")


class ProviderClient(Protocol):
    """High-level provider client boundary."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> ProviderResponse:
        ...


class TransportProviderClient:
    """Provider client using the centralized transport boundary."""

    def __init__(
        self,
        transport: ProviderTransport,
        *,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._transport = transport
        self._retry_policy = retry_policy or RetryPolicy()

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> ProviderResponse:
        request = ProviderRequest(
            method=method.upper(),
            url=url,
            headers=dict(headers or {}),
            body=body,
        )

        last_error: ProviderTransportError | None = None

        for _ in range(self._retry_policy.max_attempts):
            try:
                return self._transport.send(request)
            except ProviderTransportError as exc:
                last_error = exc

        assert last_error is not None
        raise last_error
