"""Unit Tests for Static AST Dependency Graph Builder (Phase 11L Stage 3)."""

import pytest

from app.testing.impact.contracts import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyRelationType,
)
from app.testing.impact.graph import ASTDependencyGraphBuilder


class TestASTDependencyGraph:
    """Comprehensive tests for ASTDependencyGraphBuilder and DependencyGraph."""

    def test_build_graph_nodes_and_edges(self) -> None:
        """Verify graph building creates proper nodes, directed edges, and adjacency."""
        proj_id = "proj-graph-1"
        files_map = {
            "app/calculator.py": (
                "def add(a, b):\n"
                "    return a + b\n"
            ),
            "app/service.py": (
                "from app.calculator import add\n\n"
                "def calculate(x, y):\n"
                "    return add(x, y)\n"
            ),
            "tests/test_service.py": (
                "from app.service import calculate\n\n"
                "def test_calc():\n"
                "    assert calculate(1, 2) == 3\n"
            ),
        }

        builder = ASTDependencyGraphBuilder()
        graph = builder.build_graph(proj_id, files_map)

        assert graph.project_id == proj_id
        assert len(graph.nodes) == 3
        assert "app/calculator.py" in graph.nodes
        assert "app/service.py" in graph.nodes
        assert "tests/test_service.py" in graph.nodes

        # Verify node properties
        assert graph.nodes["app/calculator.py"].is_test_file is False
        assert graph.nodes["tests/test_service.py"].is_test_file is True
        assert graph.nodes["app/service.py"].language == "python"

        # Verify edges: app/service.py -> app/calculator.py
        # tests/test_service.py -> app/service.py
        assert len(graph.edges) == 2
        edge_1 = next(e for e in graph.edges if e.source_file == "app/service.py")
        assert edge_1.target_file == "app/calculator.py"

        # Verify forward adjacency (source depends on target)
        assert graph.get_direct_dependencies("app/service.py") == ["app/calculator.py"]
        assert graph.get_direct_dependencies("tests/test_service.py") == ["app/service.py"]

        # Verify reverse adjacency (target is depended on by source)
        assert graph.get_direct_dependents("app/calculator.py") == ["app/service.py"]
        assert graph.get_direct_dependents("app/service.py") == ["tests/test_service.py"]

    def test_transitive_dependents_closure_and_cycle_protection(self) -> None:
        """Verify cycle-safe transitive closure calculation."""
        proj_id = "proj-cycle"
        # Circular imports: A -> B -> C -> A
        files_map = {
            "app/module_a.py": "from app.module_b import b_func\n",
            "app/module_b.py": "from app.module_c import c_func\n",
            "app/module_c.py": "from app.module_a import a_func\n",
            "app/consumer.py": "from app.module_a import a_func\n",
        }

        builder = ASTDependencyGraphBuilder()
        graph = builder.build_graph(proj_id, files_map)

        # Transitive dependents of module_c:
        # B depends on C
        # A depends on B
        # C depends on A
        # consumer depends on A
        closure = graph.get_transitive_dependents(["app/module_c.py"])
        assert "app/module_b.py" in closure
        assert "app/module_a.py" in closure
        assert "app/consumer.py" in closure
        # Does not infinite loop, deterministically returns sorted unique list
        assert len(closure) == len(set(closure))

    def test_relative_imports_resolution(self) -> None:
        """Verify intra-package relative imports (e.g. from .utils import helper)."""
        proj_id = "proj-relative"
        files_map = {
            "app/utils.py": "def helper(): pass\n",
            "app/service.py": "from .utils import helper\ndef run(): helper()\n",
        }

        builder = ASTDependencyGraphBuilder()
        graph = builder.build_graph(proj_id, files_map)

        assert graph.get_direct_dependents("app/utils.py") == ["app/service.py"]
        assert graph.get_direct_dependencies("app/service.py") == ["app/utils.py"]

    def test_unsupported_language_files(self) -> None:
        """Verify non-Python files are cataloged with language='unsupported'."""
        proj_id = "proj-unsupported"
        files_map = {
            "frontend/app.js": "console.log('hello');",
            "config/settings.json": '{"debug": true}',
            "styles/main.css": "body { margin: 0; }",
            "app/main.py": "import os\n",
        }

        builder = ASTDependencyGraphBuilder()
        graph = builder.build_graph(proj_id, files_map)

        assert graph.nodes["frontend/app.js"].language == "unsupported"
        assert graph.nodes["config/settings.json"].language == "unsupported"
        assert graph.nodes["styles/main.css"].language == "unsupported"
        assert graph.nodes["app/main.py"].language == "python"

    def test_dynamic_imports_flagged_as_uncertain(self) -> None:
        """Verify dynamic import calls are recorded in uncertain_dependencies."""
        proj_id = "proj-dynamic"
        files_map = {
            "app/plugin_loader.py": (
                "def load_plugin(name):\n"
                "    return __import__(name)\n"
            ),
            "app/importlib_loader.py": (
                "import importlib\n"
                "def load(mod):\n"
                "    return importlib.import_module(mod)\n"
            ),
        }

        builder = ASTDependencyGraphBuilder()
        graph = builder.build_graph(proj_id, files_map)

        assert graph.nodes["app/plugin_loader.py"].has_dynamic_imports is True
        assert graph.nodes["app/importlib_loader.py"].has_dynamic_imports is True

        reasons = [u.reason for u in graph.uncertain_dependencies]
        assert "DYNAMIC_IMPORT_CALL" in reasons
        assert "IMPORTLIB_DYNAMIC_IMPORT" in reasons

    def test_syntax_error_file_handled_gracefully(self) -> None:
        """Verify unparseable Python syntax errors do not crash graph building."""
        proj_id = "proj-broken"
        files_map = {
            "app/broken.py": "def broken_syntax(:\n    pass\n",
            "app/valid.py": "def valid(): pass\n",
        }

        builder = ASTDependencyGraphBuilder()
        graph = builder.build_graph(proj_id, files_map)

        assert graph.nodes["app/broken.py"].has_syntax_error is True
        assert len(graph.uncertain_dependencies) >= 1
        assert any(u.file_path == "app/broken.py" and u.reason == "SYNTAX_ERROR" for u in graph.uncertain_dependencies)
        assert graph.nodes["app/valid.py"].has_syntax_error is False

    def test_deterministic_repeated_graph_building(self) -> None:
        """Verify repeated graph construction yields equivalent structures."""
        proj_id = "proj-det"
        files_map = {
            "app/a.py": "from app.b import b_fn\n",
            "app/b.py": "def b_fn(): pass\n",
        }

        builder = ASTDependencyGraphBuilder()
        g1 = builder.build_graph(proj_id, files_map)
        g2 = builder.build_graph(proj_id, files_map)

        assert g1.forward_adjacency == g2.forward_adjacency
        assert g1.reverse_adjacency == g2.reverse_adjacency
        assert [e.source_file for e in g1.edges] == [e.source_file for e in g2.edges]
