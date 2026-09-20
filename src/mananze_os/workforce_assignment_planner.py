"""Mananze OS workforce assignment planner foundation."""

from mananze_os.workforce_assignment import WorkforceAssignment
from mananze_os.workforce_registry import WorkforceRegistry


class WorkforceAssignmentPlanner:
    """Assign registered workforce roles to execution graph nodes."""

    def __init__(self, registry: WorkforceRegistry) -> None:
        self.registry = registry

    def assign(
        self,
        assignment_id: str,
        execution_id: str,
        node_id: str,
        role_id: str,
    ) -> WorkforceAssignment:
        self.registry.get(role_id)

        return WorkforceAssignment(
            assignment_id=assignment_id,
            execution_id=execution_id,
            node_id=node_id,
            role_id=role_id,
        )


__all__ = ["WorkforceAssignmentPlanner"]
