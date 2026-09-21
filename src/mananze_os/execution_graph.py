"""Mananze OS execution graph foundation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionNode:
    node_id: str
    capability_id: str
    skill_ids: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id is required")

        if not self.capability_id.strip():
            raise ValueError("capability_id is required")

        if any(not skill_id.strip() for skill_id in self.skill_ids):
            raise ValueError("skill_id is required")


@dataclass(frozen=True)
class ExecutionGraph:
    graph_id: str
    nodes: tuple[ExecutionNode, ...]

    def __post_init__(self) -> None:
        if not self.graph_id.strip():
            raise ValueError("graph_id is required")

        node_ids = tuple(node.node_id for node in self.nodes)

        if len(node_ids) != len(set(node_ids)):
            raise ValueError("duplicate node_id detected")

        node_id_set = set(node_ids)

        for node in self.nodes:
            if node.node_id in node.dependencies:
                raise ValueError(
                    f"node cannot depend on itself: {node.node_id}"
                )

            for dependency in node.dependencies:
                if dependency not in node_id_set:
                    raise ValueError(
                        f"unknown dependency: {dependency}"
                    )

        self._validate_acyclic()

    def _validate_acyclic(self) -> None:
        nodes_by_id = {
            node.node_id: node
            for node in self.nodes
        }

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ValueError(
                    f"execution graph contains a cycle at: {node_id}"
                )

            if node_id in visited:
                return

            visiting.add(node_id)

            for dependency in nodes_by_id[node_id].dependencies:
                visit(dependency)

            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in nodes_by_id:
            visit(node_id)

    def execution_order(self) -> tuple[str, ...]:
        """Return node IDs in dependency-safe execution order."""

        nodes_by_id = {
            node.node_id: node
            for node in self.nodes
        }

        ordered: list[str] = []
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visited:
                return

            for dependency in nodes_by_id[node_id].dependencies:
                visit(dependency)

            visited.add(node_id)
            ordered.append(node_id)

        for node_id in nodes_by_id:
            visit(node_id)

        return tuple(ordered)


__all__ = [
    "ExecutionNode",
    "ExecutionGraph",
]
