"""Tests for the Mananze OS execution graph foundation."""

import pytest

from mananze_os.execution_graph import ExecutionGraph, ExecutionNode


def test_execution_node_accepts_valid_definition() -> None:
    node = ExecutionNode(
        node_id="marketing",
        capability_id="marketing",
    )

    assert node.node_id == "marketing"
    assert node.capability_id == "marketing"
    assert node.dependencies == ()


def test_execution_node_accepts_dependencies() -> None:
    node = ExecutionNode(
        node_id="sales",
        capability_id="sales",
        dependencies=("marketing",),
    )

    assert node.dependencies == ("marketing",)


def test_execution_node_requires_node_id() -> None:
    with pytest.raises(ValueError, match="node_id is required"):
        ExecutionNode(
            node_id="",
            capability_id="marketing",
        )


def test_execution_node_requires_capability_id() -> None:
    with pytest.raises(ValueError, match="capability_id is required"):
        ExecutionNode(
            node_id="marketing",
            capability_id="",
        )


def test_execution_graph_accepts_valid_definition() -> None:
    graph = ExecutionGraph(
        graph_id="graph:001",
        nodes=(
            ExecutionNode(
                node_id="marketing",
                capability_id="marketing",
            ),
            ExecutionNode(
                node_id="sales",
                capability_id="sales",
                dependencies=("marketing",),
            ),
        ),
    )

    assert graph.graph_id == "graph:001"
    assert len(graph.nodes) == 2


def test_execution_graph_requires_graph_id() -> None:
    with pytest.raises(ValueError, match="graph_id is required"):
        ExecutionGraph(
            graph_id="",
            nodes=(),
        )
"""Tests for Mananze OS execution graph validation."""

import pytest

from mananze_os.execution_graph import ExecutionGraph, ExecutionNode


def test_execution_graph_rejects_duplicate_node_ids() -> None:
    with pytest.raises(ValueError, match="duplicate node_id detected"):
        ExecutionGraph(
            graph_id="graph:duplicate",
            nodes=(
                ExecutionNode(
                    node_id="marketing",
                    capability_id="marketing",
                ),
                ExecutionNode(
                    node_id="marketing",
                    capability_id="sales",
                ),
            ),
        )


def test_execution_graph_rejects_unknown_dependency() -> None:
    with pytest.raises(ValueError, match="unknown dependency: missing"):
        ExecutionGraph(
            graph_id="graph:unknown-dependency",
            nodes=(
                ExecutionNode(
                    node_id="sales",
                    capability_id="sales",
                    dependencies=("missing",),
                ),
            ),
        )


def test_execution_graph_rejects_self_dependency() -> None:
    with pytest.raises(
        ValueError,
        match="node cannot depend on itself: marketing",
    ):
        ExecutionGraph(
            graph_id="graph:self-dependency",
            nodes=(
                ExecutionNode(
                    node_id="marketing",
                    capability_id="marketing",
                    dependencies=("marketing",),
                ),
            ),
        )


def test_execution_graph_allows_valid_dependency_chain() -> None:
    graph = ExecutionGraph(
        graph_id="graph:valid",
        nodes=(
            ExecutionNode(
                node_id="marketing",
                capability_id="marketing",
            ),
            ExecutionNode(
                node_id="sales",
                capability_id="sales",
                dependencies=("marketing",),
            ),
            ExecutionNode(
                node_id="revenue",
                capability_id="revenue",
                dependencies=("sales",),
            ),
        ),
    )

    assert len(graph.nodes) == 3
def test_execution_graph_rejects_cycles() -> None:
    with pytest.raises(
        ValueError,
        match="execution graph contains a cycle at:",
    ):
        ExecutionGraph(
            graph_id="graph:cycle",
            nodes=(
                ExecutionNode(
                    node_id="marketing",
                    capability_id="marketing",
                    dependencies=("revenue",),
                ),
                ExecutionNode(
                    node_id="sales",
                    capability_id="sales",
                    dependencies=("marketing",),
                ),
                ExecutionNode(
                    node_id="revenue",
                    capability_id="revenue",
                    dependencies=("sales",),
                ),
            ),
        )


def test_execution_graph_returns_dependency_safe_order() -> None:
    graph = ExecutionGraph(
        graph_id="graph:order",
        nodes=(
            ExecutionNode(
                node_id="revenue",
                capability_id="revenue",
                dependencies=("sales",),
            ),
            ExecutionNode(
                node_id="marketing",
                capability_id="marketing",
            ),
            ExecutionNode(
                node_id="sales",
                capability_id="sales",
                dependencies=("marketing",),
            ),
        ),
    )

    assert graph.execution_order() == (
        "marketing",
        "sales",
        "revenue",
    )

def test_execution_node_accepts_required_skills() -> None:
    node = ExecutionNode(
        node_id="node:sales",
        capability_id="sales",
        skill_ids=("sales:lead_qualification",),
    )

    assert node.skill_ids == ("sales:lead_qualification",)


def test_execution_node_rejects_blank_skill_id() -> None:
    with pytest.raises(ValueError, match="skill_id is required"):
        ExecutionNode(
            node_id="node:sales",
            capability_id="sales",
            skill_ids=(" ",),
        )
