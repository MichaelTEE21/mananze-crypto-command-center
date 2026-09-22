"""Mananze OS structured inter-agent communication contracts."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal


IPCMessageType = Literal[
    "task_request",
    "task_result",
    "handoff",
    "evidence",
    "status",
    "failure",
    "approval",
    "policy",
    "resource",
    "cancellation",
    "escalation",
]


@dataclass(frozen=True)
class IPCMessage:
    """Validated structured message exchanged inside the Mananze OS."""

    message_id: str
    tenant_id: str
    sender_id: str
    recipient_id: str
    message_type: IPCMessageType
    correlation_id: str
    execution_id: str
    task_id: str
    payload: Any
    timestamp: datetime

    parent_message_id: str | None = None

    def __post_init__(self) -> None:
        required_fields = {
            "message_id": self.message_id,
            "tenant_id": self.tenant_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "correlation_id": self.correlation_id,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
        }

        for field_name, value in required_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")

        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime")

        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

        if self.parent_message_id is not None and not self.parent_message_id.strip():
            raise ValueError("parent_message_id cannot be blank")


class IPCMessageFactory:
    """Creates structured IPC messages with controlled defaults."""

    @staticmethod
    def create(
        *,
        message_id: str,
        tenant_id: str,
        sender_id: str,
        recipient_id: str,
        message_type: IPCMessageType,
        correlation_id: str,
        execution_id: str,
        task_id: str,
        payload: Any,
        parent_message_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> IPCMessage:
        return IPCMessage(
            message_id=message_id,
            tenant_id=tenant_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            correlation_id=correlation_id,
            execution_id=execution_id,
            task_id=task_id,
            payload=payload,
            timestamp=timestamp or datetime.now(timezone.utc),
            parent_message_id=parent_message_id,
        )


__all__ = [
    "IPCMessage",
    "IPCMessageFactory",
    "IPCMessageType",
]
