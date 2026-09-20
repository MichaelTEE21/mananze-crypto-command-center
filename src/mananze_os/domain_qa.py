"""Mananze OS domain quality-assurance foundation."""

from dataclasses import dataclass

from mananze_os.workforce_planner import DynamicWorkforcePlan


@dataclass(frozen=True)
class QAVerdict:
    work_order_id: str
    passed: bool
    checks: tuple[str, ...]


class DomainQA:
    """Verify that a dynamically planned workforce is structurally valid."""

    def verify(self, workforce: DynamicWorkforcePlan) -> QAVerdict:
        if not workforce.work_order_id.strip():
            return QAVerdict(
                work_order_id=workforce.work_order_id,
                passed=False,
                checks=("work order identity is missing",),
            )

        if not workforce.objective.strip():
            return QAVerdict(
                work_order_id=workforce.work_order_id,
                passed=False,
                checks=("work order objective is missing",),
            )

        if not workforce.roles:
            return QAVerdict(
                work_order_id=workforce.work_order_id,
                passed=False,
                checks=("no workforce capabilities selected",),
            )

        role_ids = [role.role_id for role in workforce.roles]

        if len(role_ids) != len(set(role_ids)):
            return QAVerdict(
                work_order_id=workforce.work_order_id,
                passed=False,
                checks=("duplicate workforce capability detected",),
            )

        missing_capability_ids = [
            role.role_id
            for role in workforce.roles
            if not role.capability_id.strip()
        ]

        if missing_capability_ids:
            return QAVerdict(
                work_order_id=workforce.work_order_id,
                passed=False,
                checks=("workforce contains a role without a capability ID",),
            )

        return QAVerdict(
            work_order_id=workforce.work_order_id,
            passed=True,
            checks=(
                "work order identity present",
                "objective present",
                "workforce capabilities selected",
                "no duplicate capabilities",
                "capability identifiers present",
            ),
        )


__all__ = ["QAVerdict", "DomainQA"]
