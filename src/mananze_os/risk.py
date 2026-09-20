"""Mananze OS risk classification contracts."""

from typing import Literal


RiskLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


__all__ = ["RiskLevel"]
