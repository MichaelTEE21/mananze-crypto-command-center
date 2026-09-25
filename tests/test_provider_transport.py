"""Tests for the Mananze OS provider transport."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from mananze_os.provider_transport import (
    EnvironmentCredentialProvider,
    HttpProviderTransport,
    ProviderRequest,
    ProviderResponse,
    ProviderTransportError,
)


def test_environment_credential_provider_returns_value() -> None:
    provider = EnvironmentCredentialProvider({"API_KEY": "secret-value"})

    assert provider.get("API_KEY") == "secret-value"


def test_environment_credential_provider_returns_none_for_missing_value() -> None:
    provider = EnvironmentCredentialProvider({})

    assert provider.get("MISSING") is None


def test_environment_credential_provider_ignores_blank_value() -> None:
    provider = EnvironmentCredentialProvider({"API_KEY": "   "})

    assert provider.get("API_KEY") is None


def test_provider_request_preserves_request_data() -> None:
    request = ProviderRequest(
        method="post",
        url="https://example.test/api",
        headers={"Authorization": "Bearer secret"},
        body=b'{"hello":"world"}',
        timeout_seconds=15.0,
    )

    assert request.method == "post"
    assert request.url == "https://example.test/api"
    assert request.headers["Authorization"] == "Bearer secret"
    assert request.body == b'{"hello":"world"}'
    assert request.timeout_seconds == 15.0


def test_http_transport_returns_response() -> None:
    class FakeResponse:
        status = 200

        headers = {
            "Content-Type": "application/json",
        }

        def read(self) -> bytes:
            return b'{"ok":true}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch(
        "mananze_os.provider_transport.urlopen",
        return_value=FakeResponse(),
    ) as mocked:
        response = HttpProviderTransport().send(
            ProviderRequest(
                method="POST",
                url="https://example.test/api",
                headers={"Content-Type": "application/json"},
                body=b"{}",
                timeout_seconds=10.0,
            )
        )

    assert response == ProviderResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body=b'{"ok":true}',
    )

    mocked.assert_called_once()

    request_arg = mocked.call_args.args[0]
    assert request_arg.get_method() == "POST"
    assert request_arg.full_url == "https://example.test/api"
    assert request_arg.data == b"{}"
    assert mocked.call_args.kwargs["timeout"] == 10.0


def test_http_transport_wraps_http_error() -> None:
    from urllib.error import HTTPError

    error = HTTPError(
        "https://example.test/api",
        401,
        "Unauthorized",
        {},
        None,
    )

    with patch(
        "mananze_os.provider_transport.urlopen",
        side_effect=error,
    ):
        with pytest.raises(ProviderTransportError, match="HTTP 401"):
            HttpProviderTransport().send(
                ProviderRequest(
                    method="GET",
                    url="https://example.test/api",
                    headers={},
                )
            )


def test_http_transport_wraps_network_error() -> None:
    from urllib.error import URLError

    with patch(
        "mananze_os.provider_transport.urlopen",
        side_effect=URLError("connection refused"),
    ):
        with pytest.raises(ProviderTransportError, match="transport failed"):
            HttpProviderTransport().send(
                ProviderRequest(
                    method="GET",
                    url="https://example.test/api",
                    headers={},
                )
            )


def test_http_transport_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        HttpProviderTransport().send(
            ProviderRequest(
                method="GET",
                url="https://example.test/api",
                headers={},
                timeout_seconds=0,
            )
        )
