"""Polyglot Code Intelligence Service for Phase 14.

Primary entry point for multi-language source code analysis, deterministic
incremental caching, dependency graph generation, and affected consumer traversal.
"""

from collections import deque
import hashlib
import logging
from typing import Any, Sequence
import uuid

from app.code_intelligence.contracts import (
    CodeFile,
    CodeLanguage,
    PolyglotDependencyGraph,
)
from app.code_intelligence.detector import LanguageDetector
from app.code_intelligence.graph_builder import PolyglotDependencyGraphBuilder
from app.code_intelligence.registry import LanguageAdapterRegistry, get_default_registry

logger = logging.getLogger(__name__)


class PolyglotCodeIntelligenceService:
    """Authoritative service for polyglot code intelligence and dependency analysis."""

    def __init__(
        self,
        registry: LanguageAdapterRegistry | None = None,
        graph_builder: PolyglotDependencyGraphBuilder | None = None,
    ) -> None:
        self.registry = registry or get_default_registry()
        self.graph_builder = graph_builder or PolyglotDependencyGraphBuilder(self.registry)
        # Incremental compound cache: (project_id, norm_path, content_hash) -> CodeFile
        self._file_cache: dict[tuple[str, str, str], CodeFile] = {}

    def analyze_file(
        self,
        file_path: str,
        content: str,
        project_id: str | None = None,
    ) -> CodeFile:
        """Analyze a single file with deterministic project/path/content caching."""
        norm_path = file_path.replace("\\", "/").strip("/")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        cache_key = (project_id or "", norm_path, content_hash)

        # Check incremental cache
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        lang = LanguageDetector.detect(norm_path, content)
        adapter = self.registry.get_adapter(lang)

        if adapter:
            code_file = adapter.safe_parse(norm_path, content)
        else:
            code_file = CodeFile(
                file_path=norm_path,
                language=lang,
                is_test_file=LanguageDetector.is_test_file(norm_path),
                content_hash=content_hash,
                has_syntax_error=False,
            )

        self._file_cache[cache_key] = code_file
        return code_file

    def build_project_graph(
        self,
        project_id: uuid.UUID | str,
        files_map: dict[str, str],
    ) -> PolyglotDependencyGraph:
        """Compile complete multi-language dependency graph across all project files."""
        return self.graph_builder.build_graph(project_id, files_map)

    def get_language_breakdown(self, files_map: dict[str, str]) -> dict[str, Any]:
        """Produce language distribution inventory for a file mapping."""
        breakdown: dict[str, int] = {}
        for path, content in files_map.items():
            lang = LanguageDetector.detect(path, content)
            breakdown[lang.value] = breakdown.get(lang.value, 0) + 1

        total_files = len(files_map)
        percentages = {
            lang: round((count / total_files) * 100, 1) if total_files > 0 else 0.0
            for lang, count in breakdown.items()
        }

        return {
            "total_files": total_files,
            "counts": dict(sorted(breakdown.items())),
            "percentages": dict(sorted(percentages.items())),
            "supported_languages": [l.value for l in self.registry.supported_languages()],
        }

    def find_affected_files(
        self,
        changed_files: Sequence[str],
        graph: PolyglotDependencyGraph,
        max_depth: int = 50,
    ) -> set[str]:
        """Compute transitive reverse-dependency closure of all files affected by modifications.
        
        If file A is changed, any file B that imports A (reverse dependency) is affected.
        """
        affected: set[str] = set()
        queue: deque[tuple[str, int]] = deque()

        norm_changed = {f.replace("\\", "/").strip("/") for f in changed_files}

        for f in norm_changed:
            if f in graph.files:
                affected.add(f)
                queue.append((f, 0))

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue

            # Traverse reverse dependencies (dependents that import `current`)
            dependents = graph.reverse_adjacency.get(current, [])
            for dep in dependents:
                if dep not in affected:
                    affected.add(dep)
                    queue.append((dep, depth + 1))

        return affected
