"""External HTTP transport for Mananze OS providers.

This module is deliberately provider-agnostic. Provider adapters construct
requests; this transport performs the actual HTTP exchange.

Credentials must be supplied through request headers or an external
credential provider. Secrets are never stored in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class CredentialProvider(Protocol):
    def get(self, name: str) -> str | None:
        ...


class EnvironmentCredentialProvider:
    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        import os

        self._environ = environ if environ is not None else os.environ

    def get(self, name: str) -> str | None:
        value = self._environ.get(name)

        if value is None:
            return None

        value = value.strip()
        return value or None


@dataclass(frozen=True)
class ProviderRequest:
    method: str
    url: str
    headers: Mapping[str, str]
    body: bytes | None = None
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class ProviderResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class ProviderTransportError(RuntimeError):
    """Raised when an external provider transport cannot complete a request."""


class ProviderTransport(Protocol):
    def send(self, request: ProviderRequest) -> ProviderResponse:
        ...


class HttpProviderTransport:
    """Concrete HTTP/HTTPS transport using Python's standard library."""

    def send(self, request: ProviderRequest) -> ProviderResponse:
        if not request.method.strip():
            raise ValueError("HTTP method is required")

        if not request.url.strip():
            raise ValueError("URL is required")

        if request.timeout_seconds is not None and request.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        http_request = Request(
            url=request.url,
            data=request.body,
            headers=dict(request.headers),
            method=request.method.upper(),
        )

        try:
            with urlopen(
                http_request,
                timeout=request.timeout_seconds,
            ) as response:
                return ProviderResponse(
                    status_code=response.status,
                    headers=dict(response.headers.items()),
                    body=response.read(),
                )

        except HTTPError as exc:
            try:
                body = exc.read()
            except Exception:
                body = b""

            raise ProviderTransportError(
                f"provider returned HTTP {exc.code}: {exc.reason}; "
                f"body={body[:1000]!r}"
            ) from exc

        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderTransportError(
                f"provider transport failed: {exc}"
            ) from exc


__all__ = [
    "CredentialProvider",
    "EnvironmentCredentialProvider",
    "HttpProviderTransport",
    "ProviderRequest",
    "ProviderResponse",
    "ProviderTransport",
    "ProviderTransportError",
]
