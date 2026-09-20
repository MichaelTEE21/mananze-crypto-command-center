"""Mananze OS workforce coordination fabric foundation."""

from mananze_os.workforce_assignment import WorkforceAssignment
from mananze_os.workforce_assignment_planner import WorkforceAssignmentPlanner
from mananze_os.workforce_registry import WorkforceRegistry
from mananze_os.workforce_role import WorkforceRole


class WorkforceFabric:
    """Coordinate workforce roles and controlled assignments."""

    def __init__(
        self,
        registry: WorkforceRegistry | None = None,
    ) -> None:
        self.registry = registry or WorkforceRegistry()
        self.assignment_planner = WorkforceAssignmentPlanner(
            self.registry
        )
        self._assignments: dict[str, WorkforceAssignment] = {}

    def register_role(self, role: WorkforceRole) -> None:
        self.registry.register(role)

    def get_role(self, role_id: str) -> WorkforceRole:
        return self.registry.get(role_id)

    def list_roles(self) -> tuple[WorkforceRole, ...]:
        return self.registry.list_all()

    def assign_role(
        self,
        assignment_id: str,
        execution_id: str,
        node_id: str,
        role_id: str,
    ) -> WorkforceAssignment:
        if assignment_id in self._assignments:
            raise ValueError(
                f"assignment already exists: {assignment_id}"
            )

        assignment = self.assignment_planner.assign(
            assignment_id=assignment_id,
            execution_id=execution_id,
            node_id=node_id,
            role_id=role_id,
        )

        self._assignments[assignment.assignment_id] = assignment
        return assignment

    def get_assignment(
        self,
        assignment_id: str,
    ) -> WorkforceAssignment:
        try:
            return self._assignments[assignment_id]
        except KeyError:
            raise KeyError(
                f"unknown workforce assignment: {assignment_id}"
            ) from None

    def list_assignments(self) -> tuple[WorkforceAssignment, ...]:
        return tuple(self._assignments.values())


__all__ = ["WorkforceFabric"]
