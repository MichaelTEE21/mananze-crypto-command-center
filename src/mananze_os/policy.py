"""Mananze OS governance policy contracts."""

from dataclasses import dataclass
from typing import Literal


PolicyEffect = Literal[
    "allow",
    "approval_required",
    "deny",
]


@dataclass(frozen=True)
class Policy:
    policy_id: str
    name: str
    effect: PolicyEffect
    description: str
    capability_ids: tuple[str, ...] = ()


__all__ = ["Policy", "PolicyEffect"]
