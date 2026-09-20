"""Mananze OS authority foundation contract."""

from dataclasses import dataclass
from typing import Literal


AuthorityLevel = Literal[
    "system",
    "tenant",
    "agent",
    "human",
]


@dataclass(frozen=True)
class Authority:
    actor_id: str
    level: AuthorityLevel
    can_execute: bool = False
    requires_approval: bool = True

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("actor_id is required")


__all__ = ["Authority", "AuthorityLevel"]
