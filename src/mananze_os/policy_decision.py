"""Mananze OS policy decision contract."""

from dataclasses import dataclass

from mananze_os.autonomy import AutonomyLevel
from mananze_os.policy import PolicyEffect
from mananze_os.risk import RiskLevel


@dataclass(frozen=True)
class PolicyDecision:
    work_order_id: str
    effect: PolicyEffect
    risk: RiskLevel
    autonomy_level: AutonomyLevel
    reasons: tuple[str, ...]


__all__ = ["PolicyDecision"]
