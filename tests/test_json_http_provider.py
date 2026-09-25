from unittest.mock import Mock

from mananze_os.json_http_provider import JsonHttpProvider
from mananze_os.provider import ProviderRequest
from mananze_os.provider_transport import ProviderResponse


def test_json_http_provider_executes_json_request() -> None:
    client = Mock()
    client.request.return_value = ProviderResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body=b'{"answer":"ok"}',
    )

    provider = JsonHttpProvider("test-provider", client)

    response = provider.execute(
        ProviderRequest(
            provider_id="test-provider",
            tool_id="test-tool",
            tenant_id="tenant-1",
            execution_id="execution-1",
            operation="test",
            payload={
                "url": "https://example.test/api",
                "method": "POST",
                "body": {"hello": "world"},
            },
        )
    )

    assert response.success is True
    assert response.output == {"answer": "ok"}
    assert response.provider_id == "test-provider"
    assert response.tenant_id == "tenant-1"

    client.request.assert_called_once()


def test_json_http_provider_preserves_http_failure() -> None:
    client = Mock()
    client.request.return_value = ProviderResponse(
        status_code=401,
        headers={},
        body=b'{"error":"unauthorized"}',
    )

    provider = JsonHttpProvider("test-provider", client)

    response = provider.execute(
        ProviderRequest(
            provider_id="test-provider",
            tool_id="test-tool",
            tenant_id="tenant-1",
            execution_id="execution-1",
            operation="test",
            payload={
                "url": "https://example.test/api",
                "body": {},
            },
        )
    )

    assert response.success is False
    assert response.output == {"error": "unauthorized"}
    assert response.error == "HTTP 401"


def test_json_http_provider_rejects_wrong_provider() -> None:
    client = Mock()
    provider = JsonHttpProvider("provider-a", client)

    request = ProviderRequest(
        provider_id="provider-b",
        tool_id="tool",
        tenant_id="tenant",
        execution_id="execution",
        operation="test",
        payload={"url": "https://example.test"},
    )

    try:
        provider.execute(request)
    except PermissionError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("expected PermissionError")
