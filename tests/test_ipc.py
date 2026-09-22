import pytest
from datetime import datetime, timezone

from mananze_os.ipc import IPCMessage, IPCMessageFactory


def make_message(**overrides):
    values = {
        "message_id": "msg-1",
        "tenant_id": "tenant-1",
        "sender_id": "agent-a",
        "recipient_id": "agent-b",
        "message_type": "task_request",
        "correlation_id": "corr-1",
        "execution_id": "exec-1",
        "task_id": "task-1",
        "payload": {"objective": "analyse sales"},
        "timestamp": datetime.now(timezone.utc),
    }
    values.update(overrides)
    return IPCMessage(**values)


def test_valid_ipc_message():
    message = make_message()

    assert message.message_id == "msg-1"
    assert message.tenant_id == "tenant-1"
    assert message.message_type == "task_request"


def test_factory_creates_timestamp_when_missing():
    message = IPCMessageFactory.create(
        message_id="msg-1",
        tenant_id="tenant-1",
        sender_id="agent-a",
        recipient_id="agent-b",
        message_type="task_result",
        correlation_id="corr-1",
        execution_id="exec-1",
        task_id="task-1",
        payload={"result": "complete"},
    )

    assert message.timestamp.tzinfo is not None


def test_parent_message_preserves_lineage():
    message = make_message(parent_message_id="msg-parent")

    assert message.parent_message_id == "msg-parent"


@pytest.mark.parametrize(
    "field",
    [
        "message_id",
        "tenant_id",
        "sender_id",
        "recipient_id",
        "correlation_id",
        "execution_id",
        "task_id",
    ],
)
def test_required_identity_fields_cannot_be_blank(field):
    with pytest.raises(ValueError):
        make_message(**{field: "   "})


def test_timestamp_must_be_timezone_aware():
    with pytest.raises(ValueError, match="timezone-aware"):
        make_message(timestamp=datetime(2026, 9, 22, 12, 0, 0))


def test_timestamp_must_be_datetime():
    with pytest.raises(TypeError, match="datetime"):
        make_message(timestamp="2026-09-22T12:00:00Z")


def test_blank_parent_message_is_rejected():
    with pytest.raises(ValueError, match="parent_message_id"):
        make_message(parent_message_id="   ")


def test_payload_is_preserved():
    payload = {
        "capability_id": "sales",
        "requested_action": "prepare_lead_followup",
    }

    message = make_message(payload=payload)

    assert message.payload == payload


def test_message_is_immutable():
    message = make_message()

    with pytest.raises(AttributeError):
        message.tenant_id = "tenant-2"
