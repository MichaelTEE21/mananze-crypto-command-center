"""Mananze OS input gate foundation contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InputRequest:
    request_id: str
    tenant_id: str
    actor_id: str
    objective: str
    channel: str = "web"


__all__ = ["InputRequest"]
