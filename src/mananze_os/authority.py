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


__all__ = ["Authority", "AuthorityLevel"]
