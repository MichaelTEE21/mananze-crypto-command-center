"""Mananze OS workforce assignment planner foundation."""

from mananze_os.execution_graph import ExecutionNode
from mananze_os.workforce_assignment import WorkforceAssignment
from mananze_os.workforce_registry import WorkforceRegistry


class WorkforceAssignmentPlanner:
    """Assign registered workforce roles to compatible execution graph nodes."""

    def __init__(self, registry: WorkforceRegistry) -> None:
        self.registry = registry

    def assign(
        self,
        assignment_id: str,
        execution_id: str,
        node: ExecutionNode,
        role_id: str,
    ) -> WorkforceAssignment:
        role = self.registry.get(role_id)

        if node.capability_id not in role.capability_ids:
            raise ValueError(
                f"workforce role lacks required capability: "
                f"{node.capability_id}"
            )

        for skill_id in node.skill_ids:
            if skill_id not in role.skill_ids:
                raise ValueError(
                    f"workforce role lacks required skill: {skill_id}"
                )

        return WorkforceAssignment(
            assignment_id=assignment_id,
            execution_id=execution_id,
            node_id=node.node_id,
            role_id=role_id,
        )


__all__ = ["WorkforceAssignmentPlanner"]
