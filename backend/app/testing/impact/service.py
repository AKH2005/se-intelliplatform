"""Change Impact Analysis Service (Phase 11L Stage 3).

Determines deterministic impact of source code changes across:
Changed Files -> Dependency Relationships -> Affected Files -> Affected Tests -> Affected Requirements.

Architectural Invariants:
1. Analysis Only: ZERO test execution, ZERO Docker execution, ZERO Playwright calls, ZERO LLMs.
2. Conservative Over-Selection: Unresolved/uncertain dependencies trigger broader regression flags.
3. Authoritative Links Only: Maps impacted tests to requirements strictly via requirement_links.
4. Strict Project Isolation: Rejects cross-project changes, tests, or requirements.
5. Deterministic Output: Sorted lists and deterministic report structure.
"""

from datetime import datetime
import logging
import uuid
from typing import Any, Sequence

from app.schemas.development_version import VersionComparisonResponse, VersionFileDiff
from app.testing.impact.contracts import (
    AnalysisConfidence,
    ChangeImpactReport,
    DependencyGraph,
    ImpactReason,
    UncertainDependency,
)
from app.testing.impact.errors import (
    ChangeImpactIsolationError,
    ChangeImpactValidationError,
)
from app.testing.impact.graph import ASTDependencyGraphBuilder
from app.testing.inventory.contracts import (
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
)

logger = logging.getLogger(__name__)


class ChangeImpactService:
    """Authoritative deterministic change impact analysis service."""

    def __init__(self, graph_builder: ASTDependencyGraphBuilder | None = None) -> None:
        self.graph_builder = graph_builder or ASTDependencyGraphBuilder()

    def analyze_change_impact(
        self,
        project_id: uuid.UUID | str,
        changed_files: Sequence[str] | VersionComparisonResponse | dict[str, Any],
        files_map: dict[str, str],
        inventory: UnifiedTestInventory,
        active_requirement_ids: Sequence[str] | set[str] | None = None,
        dependency_graph: DependencyGraph | None = None,
        comparison_context: dict[str, Any] | None = None,
        calculated_at: datetime | None = None,
    ) -> ChangeImpactReport:
        """Calculate deterministic change impact from source modifications.
        
        Args:
            project_id: Target project UUID or string.
            changed_files: List of modified file paths, VersionComparisonResponse, or change dict.
            files_map: Current mapping of relative project file paths to content.
            inventory: Authoritative UnifiedTestInventory from Stage 1.
            active_requirement_ids: Optional active requirement ID set for requirement impact mapping.
            dependency_graph: Optional pre-compiled DependencyGraph.
            comparison_context: Optional metadata regarding version diff.
            calculated_at: Optional fixed timestamp for deterministic testing.
            
        Returns:
            ChangeImpactReport: Complete deterministic change impact intelligence report.
            
        Raises:
            ChangeImpactIsolationError: On cross-project file, inventory, or test mismatch.
            ChangeImpactValidationError: On invalid input data.
        """
        clean_proj = str(project_id).strip().lower()
        inv_proj = str(inventory.project_id).strip().lower()

        # 1. Enforce Project Isolation on Inventory and Tests
        if clean_proj != inv_proj:
            raise ChangeImpactIsolationError(
                f"Project ID '{clean_proj}' does not match inventory project ID '{inv_proj}'."
            )

        for test in inventory.tests:
            t_proj = str(test.project_id).strip().lower()
            if t_proj != clean_proj:
                raise ChangeImpactIsolationError(
                    f"Test '{test.test_id}' belongs to project '{t_proj}', violating isolation with '{clean_proj}'."
                )

        # 2. Extract and Normalize Changed Files
        raw_changed_paths, comp_ctx = self._extract_changed_paths(changed_files, clean_proj)
        final_context = {**(comparison_context or {}), **comp_ctx}

        sorted_changed_files = sorted(list(raw_changed_paths))

        # 3. Obtain or Build Dependency Graph
        if dependency_graph is None:
            has_polyglot = any(
                p.endswith((".js", ".jsx", ".ts", ".tsx", ".java"))
                for p in sorted_changed_files
            ) or any(
                p.endswith((".js", ".jsx", ".ts", ".tsx", ".java"))
                for p in files_map.keys()
            )
            graph = self.graph_builder.build_graph(clean_proj, files_map, enable_polyglot=has_polyglot)
        else:
            graph_proj = str(dependency_graph.project_id).strip().lower()
            if graph_proj != clean_proj:
                raise ChangeImpactIsolationError(
                    f"DependencyGraph belongs to project '{graph_proj}', not '{clean_proj}'."
                )
            graph = dependency_graph

        # 4. Calculate Direct and Transitive Affected Source Files
        directly_affected: set[str] = set()
        for cf in sorted_changed_files:
            deps = graph.get_direct_dependents(cf)
            for d in deps:
                if d not in sorted_changed_files:
                    directly_affected.add(d)

        sorted_direct_affected = sorted(list(directly_affected))

        # Transitive closure across all changed files
        transitive_closure = graph.get_transitive_dependents(sorted_changed_files)
        # Transitively affected files = closure excluding directly changed files
        transitive_only = set(transitive_closure) - set(sorted_changed_files) - directly_affected
        sorted_transitive_affected = sorted(list(transitive_only))

        all_affected_files_set = set(sorted_changed_files) | directly_affected | set(transitive_closure)
        sorted_all_affected = sorted(list(all_affected_files_set))

        # 5. Evaluate Uncertainty & Conservative Over-Selection
        uncertain_files: set[str] = set()
        uncertain_deps_list: list[UncertainDependency] = []
        requires_broader_regression = False
        analysis_confidence = AnalysisConfidence.HIGH

        for cf in sorted_changed_files:
            node = graph.nodes.get(cf)
            if node:
                if node.language != "python":
                    uncertain_files.add(cf)
                    requires_broader_regression = True
                    analysis_confidence = AnalysisConfidence.MEDIUM
                    uncertain_deps_list.append(
                        UncertainDependency(
                            file_path=cf,
                            reason=f"UNSUPPORTED_LANGUAGE_{node.language.upper()}",
                        )
                    )
                if node.has_syntax_error:
                    uncertain_files.add(cf)
                    requires_broader_regression = True
                    analysis_confidence = AnalysisConfidence.LOW
                if node.has_dynamic_imports:
                    uncertain_files.add(cf)
                    requires_broader_regression = True
                    if analysis_confidence == AnalysisConfidence.HIGH:
                        analysis_confidence = AnalysisConfidence.MEDIUM
            else:
                # File changed but not present in graph nodes (e.g. deleted or outside source tree)
                uncertain_files.add(cf)
                uncertain_deps_list.append(
                    UncertainDependency(
                        file_path=cf,
                        reason="FILE_NOT_FOUND_IN_DEPENDENCY_GRAPH",
                    )
                )

        # Include graph-level uncertain dependencies associated with affected files
        for u_dep in graph.uncertain_dependencies:
            if u_dep.file_path in all_affected_files_set:
                if u_dep not in uncertain_deps_list:
                    uncertain_deps_list.append(u_dep)
                uncertain_files.add(u_dep.file_path)
                requires_broader_regression = True

        # 6. Map Affected Files to Tests in UnifiedTestInventory
        affected_tests_map: dict[str, UnifiedTestDefinition] = {}
        test_impact_reasons: dict[str, set[ImpactReason]] = {}

        # Pre-build lookup indexes from inventory
        for test in inventory.tests:
            t_file = test.metadata.get("file_path") or self._extract_file_from_ref(test.source_reference)
            target_f = test.target_file

            reasons: set[ImpactReason] = set()

            # A. Direct test file modification
            if t_file and t_file in sorted_changed_files:
                reasons.add(ImpactReason.DIRECT_TEST_FILE)
                reasons.add(ImpactReason.DIRECT_CHANGE)

            # B. Test file reached via dependency closure
            elif t_file and t_file in all_affected_files_set:
                reasons.add(ImpactReason.DEPENDENCY_CLOSURE)

            # C. Target source file is affected
            if target_f and target_f in all_affected_files_set:
                reasons.add(ImpactReason.DEPENDENCY_CLOSURE)

            # D. Browser tier tests
            if test.tier in (TestTier.BROWSER_SMOKE, TestTier.BROWSER_JOURNEY):
                # Check route references against affected symbols or files
                routes = test.metadata.get("routes", [])
                if test.target_symbol and test.target_symbol.startswith("/"):
                    routes.append(test.target_symbol)

                # If backend route handlers or main entrypoint was modified
                route_impact = any(
                    "route" in f or "api" in f or "main" in f or "view" in f
                    for f in all_affected_files_set
                )
                if route_impact:
                    reasons.add(ImpactReason.BROWSER_ROUTE_OVERLAP)

                # Conservative fallback: if dynamic uncertainty requires broader regression, include browser tests
                if requires_broader_regression:
                    reasons.add(ImpactReason.UNKNOWN_DEPENDENCY)

            if reasons:
                affected_tests_map[test.test_id] = test
                if test.test_id not in test_impact_reasons:
                    test_impact_reasons[test.test_id] = set()
                test_impact_reasons[test.test_id].update(reasons)

        sorted_affected_test_ids = sorted(affected_tests_map.keys())
        sorted_affected_tests = [affected_tests_map[tid] for tid in sorted_affected_test_ids]

        # 7. Map Affected Tests to Requirements
        active_req_set = {str(r).strip() for r in (active_requirement_ids or []) if str(r).strip()}

        affected_reqs_set: set[str] = set()
        req_impact_reasons: dict[str, set[ImpactReason]] = {}

        for test in sorted_affected_tests:
            # Stage 3 Invariant: Only authoritative requirement_links count!
            for req_link in test.requirement_links:
                clean_req = str(req_link).strip()
                if not active_req_set or clean_req in active_req_set:
                    affected_reqs_set.add(clean_req)
                    if clean_req not in req_impact_reasons:
                        req_impact_reasons[clean_req] = set()
                    req_impact_reasons[clean_req].add(ImpactReason.AUTHORITATIVE_REQUIREMENT_LINK)
                    # Inherit reasons from test
                    req_impact_reasons[clean_req].update(test_impact_reasons.get(test.test_id, set()))

        sorted_affected_reqs = sorted(list(affected_reqs_set))

        # Format final reason dictionaries deterministically
        final_test_reasons: dict[str, list[ImpactReason]] = {
            tid: sorted(list(reasons), key=lambda r: r.value)
            for tid, reasons in test_impact_reasons.items()
        }
        final_req_reasons: dict[str, list[ImpactReason]] = {
            rid: sorted(list(reasons), key=lambda r: r.value)
            for rid, reasons in req_impact_reasons.items()
        }

        report_kwargs: dict[str, Any] = {
            "project_id": clean_proj,
            "changed_files": sorted_changed_files,
            "directly_affected_files": sorted_direct_affected,
            "transitively_affected_files": sorted_transitive_affected,
            "all_affected_files": sorted_all_affected,
            "affected_tests": sorted_affected_tests,
            "affected_test_ids": sorted_affected_test_ids,
            "test_impact_reasons": final_test_reasons,
            "affected_requirements": sorted_affected_reqs,
            "requirement_impact_reasons": final_req_reasons,
            "uncertain_files": sorted(list(uncertain_files)),
            "uncertain_dependencies": uncertain_deps_list,
            "requires_broader_regression": requires_broader_regression,
            "analysis_confidence": analysis_confidence,
            "comparison_context": final_context,
            "metadata": {
                "changed_count": len(sorted_changed_files),
                "affected_files_count": len(sorted_all_affected),
                "affected_tests_count": len(sorted_affected_test_ids),
                "affected_requirements_count": len(sorted_affected_reqs),
            },
        }
        if calculated_at is not None:
            report_kwargs["calculated_at"] = calculated_at

        return ChangeImpactReport(**report_kwargs)

    # ==========================================================================
    # Helpers
    # ==========================================================================

    def _extract_changed_paths(
        self,
        changed_files: Sequence[str] | VersionComparisonResponse | dict[str, Any],
        project_id: str,
    ) -> tuple[set[str], dict[str, Any]]:
        """Normalize changed files from list, VersionComparisonResponse, or raw dict."""
        paths: set[str] = set()
        context: dict[str, Any] = {}

        if isinstance(changed_files, VersionComparisonResponse):
            context["from_version_id"] = str(changed_files.from_version_id)
            context["to_version_id"] = str(changed_files.to_version_id)
            context["from_version_number"] = changed_files.from_version_number
            context["to_version_number"] = changed_files.to_version_number

            for diff in changed_files.files_added:
                paths.add(diff.path.replace("\\", "/").strip("/"))
            for diff in changed_files.files_modified:
                paths.add(diff.path.replace("\\", "/").strip("/"))
            for diff in changed_files.files_removed:
                paths.add(diff.path.replace("\\", "/").strip("/"))

        elif isinstance(changed_files, dict):
            # Check for version comparison style dict
            if "files_modified" in changed_files or "files_added" in changed_files:
                for d in changed_files.get("files_added", []):
                    p = d.path if hasattr(d, "path") else d.get("path")
                    if p:
                        paths.add(str(p).replace("\\", "/").strip("/"))
                for d in changed_files.get("files_modified", []):
                    p = d.path if hasattr(d, "path") else d.get("path")
                    if p:
                        paths.add(str(p).replace("\\", "/").strip("/"))
                for d in changed_files.get("files_removed", []):
                    p = d.path if hasattr(d, "path") else d.get("path")
                    if p:
                        paths.add(str(p).replace("\\", "/").strip("/"))
            else:
                for p in changed_files.keys():
                    clean = str(p).replace("\\", "/").strip("/")
                    if clean:
                        paths.add(clean)

        elif isinstance(changed_files, (list, tuple, set)):
            for p in changed_files:
                clean = str(p).replace("\\", "/").strip("/")
                if clean:
                    paths.add(clean)

        else:
            raise ChangeImpactValidationError(
                f"Unsupported changed_files payload type: {type(changed_files).__name__}."
            )

        return paths, context

    def _extract_file_from_ref(self, source_ref: str) -> str | None:
        """Extract file path component from source reference string."""
        if not source_ref or source_ref.startswith("/"):
            return None
        parts = source_ref.split("::")
        cand = parts[0].strip()
        if cand.endswith(".py"):
            return cand.replace("\\", "/").strip("/")
        return None
