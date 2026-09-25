"""Generic JSON provider adapter for Mananze OS."""

from __future__ import annotations

import json
from typing import Any

from .provider import ProviderRequest, ProviderResponse
from .provider_client import ProviderClient
from .provider_transport import ProviderTransportError


class JsonHttpProvider:
    """Provider adapter for JSON-based external APIs."""

    def __init__(
        self,
        provider_id: str,
        client: ProviderClient,
        *,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id must be a non-empty string")

        self._provider_id = provider_id
        self._client = client
        self._default_headers = dict(default_headers or {})

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        if request.provider_id != self._provider_id:
            raise PermissionError(
                "request provider does not match adapter provider"
            )

        payload = request.payload

        url = payload.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("payload.url is required")

        body = payload.get("body", {})

        try:
            encoded_body = json.dumps(body).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise TypeError("payload.body must be JSON serializable") from exc

        headers = dict(self._default_headers)
        headers.update(
            {
                str(key): str(value)
                for key, value in dict(payload.get("headers", {})).items()
            }
        )

        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        method = payload.get("method", "POST")

        try:
            response = self._client.request(
                method,
                url,
                headers=headers,
                body=encoded_body,
            )
        except ProviderTransportError as exc:
            return ProviderResponse(
                provider_id=self._provider_id,
                tool_id=request.tool_id,
                tenant_id=request.tenant_id,
                execution_id=request.execution_id,
                success=False,
                output={},
                error=str(exc),
            )

        try:
            decoded = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            decoded = {"raw_body": response.body.decode("utf-8", errors="replace")}

        success = 200 <= response.status_code < 300

        return ProviderResponse(
            provider_id=self._provider_id,
            tool_id=request.tool_id,
            tenant_id=request.tenant_id,
            execution_id=request.execution_id,
            success=success,
            output=decoded if isinstance(decoded, dict) else {"data": decoded},
            error=None if success else f"HTTP {response.status_code}",
        )


__all__ = ["JsonHttpProvider"]
