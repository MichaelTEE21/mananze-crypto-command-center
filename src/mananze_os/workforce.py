"""Mananze OS workforce coordination foundation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkforceRole:
    role_id: str
    name: str
    objective: str


@dataclass(frozen=True)
class WorkforcePlan:
    work_order_id: str
    roles: tuple[WorkforceRole, ...]


class WorkforceCoordinator:
    """Assemble a controlled workforce for a compiled business plan."""

    def assign(
        self,
        work_order_id: str,
        objective: str,
    ) -> WorkforcePlan:
        if not work_order_id.strip():
            raise ValueError("work_order_id is required")

        if not objective.strip():
            raise ValueError("objective is required")

        roles = (
            WorkforceRole(
                role_id="marketing",
                name="Marketing",
                objective="Generate qualified demand.",
            ),
            WorkforceRole(
                role_id="sales",
                name="Sales",
                objective="Convert qualified demand into opportunities.",
            ),
            WorkforceRole(
                role_id="revenue",
                name="Revenue",
                objective="Convert opportunities into measurable business revenue.",
            ),
        )

        return WorkforcePlan(
            work_order_id=work_order_id,
            roles=roles,
        )


__all__ = [
    "WorkforceRole",
    "WorkforcePlan",
    "WorkforceCoordinator",
]
