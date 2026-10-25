"""Unit tests for PolyglotCodeIntelligenceService and PolyglotDependencyGraphBuilder."""

import pytest
from app.code_intelligence.contracts import CodeLanguage
from app.code_intelligence.graph_builder import PolyglotDependencyGraphBuilder
from app.code_intelligence.service import PolyglotCodeIntelligenceService


def test_polyglot_project_graph_multi_language():
    """Verify building a dependency graph across Python, JS, TS, and Java files."""
    files_map = {
        # Python
        "backend/app/main.py": "from .api import router\nimport os\n",
        "backend/app/api.py": "def router(): pass\n",

        # TypeScript
        "frontend/src/index.ts": "import { App } from './App';\n",
        "frontend/src/App.tsx": "import { helper } from './utils';\nexport function App() {}\n",
        "frontend/src/utils.ts": "export function helper() {}\n",

        # Java
        "services/src/main/java/com/corp/App.java": "package com.corp;\nimport com.corp.Model;\npublic class App {}\n",
        "services/src/main/java/com/corp/Model.java": "package com.corp;\npublic class Model {}\n",

        # Unknown / static binary asset
        "static/asset.xyz": "binary data",
    }

    service = PolyglotCodeIntelligenceService()
    graph = service.build_project_graph("proj-polyglot", files_map)

    assert graph.project_id == "proj-polyglot"
    assert len(graph.files) == 8

    # Check language breakdown
    lb = graph.language_breakdown
    assert lb["python"] == 2
    assert lb["typescript"] == 3
    assert lb["java"] == 2
    assert lb["unknown"] == 1

    # Check forward adjacency
    assert "backend/app/api.py" in graph.forward_adjacency["backend/app/main.py"]
    assert "frontend/src/App.tsx" in graph.forward_adjacency["frontend/src/index.ts"]
    assert "frontend/src/utils.ts" in graph.forward_adjacency["frontend/src/App.tsx"]
    assert "services/src/main/java/com/corp/Model.java" in graph.forward_adjacency["services/src/main/java/com/corp/App.java"]

    # Check reverse adjacency (dependents)
    assert "backend/app/main.py" in graph.reverse_adjacency["backend/app/api.py"]
    assert "frontend/src/index.ts" in graph.reverse_adjacency["frontend/src/App.tsx"]
    assert "frontend/src/App.tsx" in graph.reverse_adjacency["frontend/src/utils.ts"]


def test_transitive_affected_files_traversal():
    """Verify transitive reverse dependency closure when a leaf file changes."""
    files_map = {
        "src/leaf.ts": "export const x = 1;\n",
        "src/middle.ts": "import { x } from './leaf';\nexport const y = x + 1;\n",
        "src/top.ts": "import { y } from './middle';\nconsole.log(y);\n",
        "src/unrelated.ts": "export const z = 100;\n",
    }

    service = PolyglotCodeIntelligenceService()
    graph = service.build_project_graph("proj-transitive", files_map)

    # Change leaf.ts -> middle.ts and top.ts should be affected
    affected = service.find_affected_files(["src/leaf.ts"], graph)
    assert "src/leaf.ts" in affected
    assert "src/middle.ts" in affected
    assert "src/top.ts" in affected
    assert "src/unrelated.ts" not in affected


def test_incremental_content_hash_caching():
    """Verify identical file contents return cached CodeFile without re-parsing."""
    service = PolyglotCodeIntelligenceService()
    content = "export function doMath(a: number, b: number): number { return a + b; }"

    cf1 = service.analyze_file("src/math.ts", content)
    cf2 = service.analyze_file("src/math.ts", content)

    # Exact same cached instance
    assert cf1 is cf2

    # Modified content produces fresh analysis
    cf3 = service.analyze_file("src/math.ts", content + "\nexport const PI = 3.14;")
    assert cf3 is not cf1


def test_legacy_graph_conversion_fidelity():
    """Verify conversion of PolyglotDependencyGraph to legacy Phase 11L DependencyGraph."""
    files_map = {
        "app/main.py": "from .config import settings\n",
        "app/config.py": "settings = {}\n",
    }
    builder = PolyglotDependencyGraphBuilder()
    poly_graph = builder.build_graph("proj-conv", files_map)
    legacy_graph = builder.to_legacy_dependency_graph(poly_graph)

    assert legacy_graph.project_id == "proj-conv"
    assert "app/main.py" in legacy_graph.nodes
    assert legacy_graph.nodes["app/main.py"].language == "python"
    assert "app/config.py" in legacy_graph.forward_adjacency["app/main.py"]


def test_malformed_file_isolation():
    """Verify that a malformed file does not crash analysis of valid files."""
    files_map = {
        "src/valid.ts": "export const a = 10;\n",
        "src/broken.py": "def broken_syntax(:\n",
        "src/also_valid.js": "const b = 20;\n",
    }
    service = PolyglotCodeIntelligenceService()
    graph = service.build_project_graph("proj-malformed", files_map)

    assert len(graph.files) == 3
    assert graph.files["src/broken.py"].has_syntax_error is True
    assert graph.files["src/valid.ts"].has_syntax_error is False
    assert graph.files["src/also_valid.js"].has_syntax_error is False
    assert len(graph.uncertain_dependencies) > 0


def test_security_invariants_no_execution():
    """Verify malicious code with system calls/eval strings is never executed."""
    malicious_code = """
import os
os.system('echo dangerous')
eval('__import__("sys").exit(1)')
"""
    service = PolyglotCodeIntelligenceService()
    # Analyzing must complete purely statically without executing system/eval
    cf = service.analyze_file("untrusted/code.py", malicious_code)
    assert cf.language == CodeLanguage.PYTHON
    assert cf.has_dynamic_constructs is True


def test_cache_compound_key_and_thrashing_prevention():
    """Verify that distinct files with identical contents or across projects do not collide in cache."""
    service = PolyglotCodeIntelligenceService()
    same_content = "export const CONSTANT = 42;\n"

    # 1. Distinct files in the same project
    f1 = service.analyze_file("src/constants1.ts", same_content, project_id="proj-1")
    f2 = service.analyze_file("src/constants2.ts", same_content, project_id="proj-1")

    assert f1.file_path == "src/constants1.ts"
    assert f2.file_path == "src/constants2.ts"

    # Both must be retained in cache simultaneously without overwrite thrashing
    cache_keys = list(service._file_cache.keys())
    assert ("proj-1", "src/constants1.ts") == (cache_keys[0][0], cache_keys[0][1])
    assert ("proj-1", "src/constants2.ts") == (cache_keys[1][0], cache_keys[1][1])

    # 2. Same file path in a different project
    f3 = service.analyze_file("src/constants1.ts", same_content, project_id="proj-2")
    assert f3.file_path == "src/constants1.ts"
    assert ("proj-2", "src/constants1.ts") in [(k[0], k[1]) for k in service._file_cache.keys()]

