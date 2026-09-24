"""Mananze OS input gate foundation contract."""

from dataclasses import dataclass
from typing import Literal


ProcessingMode = Literal[
    "standard",
    "sync",
    "fast",
    "async",
    "background",
    "event",
    "batch",
]


@dataclass(frozen=True)
class InputRequest:
    request_id: str
    tenant_id: str
    actor_id: str
    objective: str
    channel: str = "web"
    processing_mode: ProcessingMode = "standard"
    candidate_capability_ids: tuple[str, ...] = ()


__all__ = ["InputRequest", "ProcessingMode"]
