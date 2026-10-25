"""Unified Test Inventory Service for Phase 11L Stage 1.

Provides deterministic, side-effect free discovery, normalization, and bidirectional
traceability indexing across all four testing tiers (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY).

Architectural Invariants:
1. Purely deterministic and read-only: ZERO test execution, ZERO shell/Docker, ZERO LLM calls.
2. Reuses existing TestDiscovery and ASTAnalyzer primitives without duplicate engines.
3. Preserves authoritative requirement links without hallucinating associations.
4. Enforces strict project isolation: rejects cross-project data contamination.
5. Deterministic identity: stable, reproducible IDs with duplicate collision detection.
"""

import ast
from datetime import datetime
import logging
import re
import uuid
from typing import Any, Sequence

from app.agents.browser_journey.contracts import BrowserJourneySuiteCandidate
from app.agents.test_generation.contracts import AITestSuite, GeneratedTest
from app.browser.contracts import DeterministicBrowserTestDefinition
from app.browser.journey.contracts import ValidatedBrowserJourney, ValidatedBrowserJourneySuite
from app.sandbox.static_analysis.ast_analyzer import ASTAnalyzer
from app.sandbox.static_analysis.test_discovery import TestDiscovery
from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    DiscoveryStatus,
    TestInventoryConflict,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
    compute_deterministic_inventory_id,
)
from app.testing.inventory.errors import (
    UnifiedTestInventoryConflictError,
    UnifiedTestInventoryIsolationError,
    UnifiedTestInventoryValidationError,
)

logger = logging.getLogger(__name__)


class UnifiedTestInventoryService:
    """Authoritative discovery and normalization service compiling the Unified Test Inventory."""

    def __init__(
        self,
        test_discovery: TestDiscovery | None = None,
        ast_analyzer: ASTAnalyzer | None = None,
    ) -> None:
        self.test_discovery = test_discovery or TestDiscovery()
        self.ast_analyzer = ast_analyzer or ASTAnalyzer()

    # ==========================================================================
    # 1. Tier-Specific Discovery and Normalization
    # ==========================================================================

    def discover_unit_tests(
        self,
        project_id: uuid.UUID | str,
        files_map: dict[str, str],
    ) -> list[UnifiedTestDefinition]:
        """Statically discover unit tests from project source files using AST analysis.
        
        Args:
            project_id: Target project UUID or string.
            files_map: Mapping of relative project file paths to source code strings.
            
        Returns:
            list[UnifiedTestDefinition]: Normalized unit test definitions.
        """
        clean_proj = str(project_id).strip().lower()
        unit_tests: list[UnifiedTestDefinition] = []

        # Sort file paths deterministically
        sorted_paths = sorted(files_map.keys())

        for file_path in sorted_paths:
            if not self.test_discovery.is_test_file(file_path):
                continue

            content = files_map[file_path]
            data, diags = self.ast_analyzer.analyze_file(file_path, content)

            if data.tree is None:
                # Syntax error or unparseable file; record partial notice if needed
                logger.warning(f"Could not parse test file '{file_path}' during unit test discovery.")
                continue

            # Detailed AST inspection to preserve class and function scope
            clean_rel_path = file_path.replace("\\", "/").strip("/")

            # Find top-level test functions and test methods in Test classes
            for node in ast.iter_child_nodes(data.tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("test_"):
                        test_node_id = f"{clean_rel_path}::{node.name}"
                        clean_id_suffix = re.sub(r"[^a-zA-Z0-9_\-]", "_", test_node_id)
                        test_id = f"unit:{clean_proj}:{clean_id_suffix}"

                        # Extract docstring if available for description
                        docstring = ast.get_docstring(node)
                        desc = docstring.strip() if docstring else None

                        unit_tests.append(
                            UnifiedTestDefinition(
                                test_id=test_id,
                                tier=TestTier.UNIT,
                                name=node.name,
                                description=desc,
                                source_reference=test_node_id,
                                project_id=clean_proj,
                                requirement_links=[],  # Authoritative links: empty unless explicitly mapped
                                inferred_requirement_links=[],
                                discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
                                target_file=self._infer_target_file(clean_rel_path, files_map),
                                target_symbol=None,
                                metadata={
                                    "file_path": clean_rel_path,
                                    "line": node.lineno,
                                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                                },
                            )
                        )

                elif isinstance(node, ast.ClassDef):
                    if node.name.startswith("Test"):
                        for member in ast.iter_child_nodes(node):
                            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                if member.name.startswith("test_"):
                                    test_node_id = f"{clean_rel_path}::{node.name}::{member.name}"
                                    clean_id_suffix = re.sub(r"[^a-zA-Z0-9_\-]", "_", test_node_id)
                                    test_id = f"unit:{clean_proj}:{clean_id_suffix}"

                                    docstring = ast.get_docstring(member)
                                    desc = docstring.strip() if docstring else None

                                    unit_tests.append(
                                        UnifiedTestDefinition(
                                            test_id=test_id,
                                            tier=TestTier.UNIT,
                                            name=f"{node.name}::{member.name}",
                                            description=desc,
                                            source_reference=test_node_id,
                                            project_id=clean_proj,
                                            requirement_links=[],
                                            inferred_requirement_links=[],
                                            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
                                            target_file=self._infer_target_file(clean_rel_path, files_map),
                                            target_symbol=None,
                                            metadata={
                                                "file_path": clean_rel_path,
                                                "class_name": node.name,
                                                "method_name": member.name,
                                                "line": member.lineno,
                                                "is_async": isinstance(member, ast.AsyncFunctionDef),
                                            },
                                        )
                                    )

        return unit_tests

    def normalize_ai_tests(
        self,
        project_id: uuid.UUID | str,
        ai_test_suite: AITestSuite,
    ) -> list[UnifiedTestDefinition]:
        """Normalize an authoritative AITestSuite into unified test definitions.
        
        Args:
            project_id: Target project UUID or string.
            ai_test_suite: Authoritative AITestSuite artifact.
            
        Returns:
            list[UnifiedTestDefinition]: Normalized AI test definitions.
            
        Raises:
            UnifiedTestInventoryIsolationError: If suite project_id does not match target.
        """
        clean_proj = str(project_id).strip().lower()
        suite_proj = str(ai_test_suite.project_id).strip().lower()

        if suite_proj != clean_proj:
            raise UnifiedTestInventoryIsolationError(
                f"AITestSuite belongs to project '{suite_proj}', cannot normalize for target '{clean_proj}'."
            )

        ai_tests: list[UnifiedTestDefinition] = []

        for t in ai_test_suite.tests:
            clean_test_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", t.test_id).strip("_")
            deterministic_id = f"ai_test:{clean_proj}:{clean_test_id}"

            # Preserve explicit authoritative requirement links
            req_links = sorted(list({str(r).strip() for r in t.requirement_ids if str(r).strip()}))

            ai_tests.append(
                UnifiedTestDefinition(
                    test_id=deterministic_id,
                    tier=TestTier.AI_TEST,
                    name=t.name,
                    description=t.description,
                    source_reference=f"{t.target_file}::{t.target_symbol or t.name}",
                    project_id=clean_proj,
                    requirement_links=req_links,
                    inferred_requirement_links=[],
                    discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
                    target_file=t.target_file,
                    target_symbol=t.target_symbol,
                    metadata={
                        "category": t.category.value if hasattr(t.category, "value") else str(t.category),
                        "rationale": t.rationale,
                        "expected_behavior": t.expected_behavior,
                        "suite_id": str(ai_test_suite.suite_id),
                    },
                )
            )

        return ai_tests

    def normalize_browser_smoke_tests(
        self,
        project_id: uuid.UUID | str,
        smoke_tests: Sequence[DeterministicBrowserTestDefinition],
    ) -> list[UnifiedTestDefinition]:
        """Normalize deterministic browser smoke test definitions.
        
        Args:
            project_id: Target project UUID or string.
            smoke_tests: Sequence of DeterministicBrowserTestDefinition instances.
            
        Returns:
            list[UnifiedTestDefinition]: Normalized browser smoke test definitions.
        """
        clean_proj = str(project_id).strip().lower()
        browser_smoke: list[UnifiedTestDefinition] = []

        for st in smoke_tests:
            clean_smoke_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", st.test_id).strip("_")
            deterministic_id = f"browser_smoke:{clean_proj}:{clean_smoke_id}"

            # Extract any explicit requirement links from metadata if present
            raw_reqs = st.metadata.get("requirement_ids", []) if st.metadata else []
            req_links = sorted(list({str(r).strip() for r in raw_reqs if str(r).strip()}))

            desc = f"Browser smoke verification targeting '{st.target_path}'"
            if st.expected_title_contains:
                desc += f" expecting title containing '{st.expected_title_contains}'"

            browser_smoke.append(
                UnifiedTestDefinition(
                    test_id=deterministic_id,
                    tier=TestTier.BROWSER_SMOKE,
                    name=st.name,
                    description=desc,
                    source_reference=st.target_path,
                    project_id=clean_proj,
                    requirement_links=req_links,
                    inferred_requirement_links=[],
                    discovery_source=DiscoveryProvenance.BROWSER_SMOKE_SUITE,
                    target_file=None,
                    target_symbol=st.target_path,
                    metadata={
                        "expected_status": st.expected_status,
                        "expected_elements": list(st.expected_elements),
                        "interactions_count": len(st.interactions),
                        "capture_screenshot": st.capture_screenshot,
                    },
                )
            )

        return browser_smoke

    def normalize_browser_journeys(
        self,
        project_id: uuid.UUID | str,
        journey_suite: ValidatedBrowserJourneySuite,
    ) -> list[UnifiedTestDefinition]:
        """Normalize an authoritatively validated browser journey suite.
        
        Args:
            project_id: Target project UUID or string.
            journey_suite: Authoritative ValidatedBrowserJourneySuite artifact.
            
        Returns:
            list[UnifiedTestDefinition]: Normalized browser journey definitions.
            
        Raises:
            UnifiedTestInventoryValidationError: If an unvalidated candidate suite is passed.
            UnifiedTestInventoryIsolationError: If suite project_id does not match target.
        """
        clean_proj = str(project_id).strip().lower()

        # Reject unvalidated candidate suites
        if isinstance(journey_suite, BrowserJourneySuiteCandidate):
            raise UnifiedTestInventoryValidationError(
                "Unvalidated BrowserJourneySuiteCandidate cannot be normalized into authoritative inventory. "
                "Supply ValidatedBrowserJourneySuite."
            )
        if not isinstance(journey_suite, ValidatedBrowserJourneySuite):
            raise UnifiedTestInventoryValidationError(
                f"Expected ValidatedBrowserJourneySuite, received {type(journey_suite).__name__}."
            )

        suite_proj = str(journey_suite.project_id).strip().lower()
        if suite_proj != clean_proj:
            raise UnifiedTestInventoryIsolationError(
                f"ValidatedBrowserJourneySuite belongs to project '{suite_proj}', cannot normalize for target '{clean_proj}'."
            )

        journeys: list[UnifiedTestDefinition] = []

        for j in journey_suite.journeys:
            clean_journey_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", j.journey_id).strip("_")
            deterministic_id = f"browser_journey:{clean_proj}:{clean_journey_id}"

            # Extract authoritative requirement links
            req_links = sorted(list({str(r).strip() for r in j.validated_requirement_ids if str(r).strip()}))

            routes_ref = ", ".join(j.validated_target_routes) if j.validated_target_routes else "/"

            journeys.append(
                UnifiedTestDefinition(
                    test_id=deterministic_id,
                    tier=TestTier.BROWSER_JOURNEY,
                    name=j.title,
                    description=j.description,
                    source_reference=routes_ref,
                    project_id=clean_proj,
                    requirement_links=req_links,
                    inferred_requirement_links=[],
                    discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
                    target_file=None,
                    target_symbol=j.validated_target_routes[0] if j.validated_target_routes else "/",
                    metadata={
                        "category": j.category.value if hasattr(j.category, "value") else str(j.category),
                        "priority": j.priority.value if hasattr(j.priority, "value") else str(j.priority),
                        "steps_count": len(j.steps),
                        "routes": list(j.validated_target_routes),
                        "preconditions": list(j.preconditions),
                        "suite_id": str(journey_suite.suite_id),
                    },
                )
            )

        return journeys

    # ==========================================================================
    # 2. Unified Inventory Aggregation & Bidirectional Indexing
    # ==========================================================================

    def build_inventory(
        self,
        project_id: uuid.UUID | str,
        files_map: dict[str, str] | None = None,
        ai_test_suite: AITestSuite | None = None,
        smoke_tests: Sequence[DeterministicBrowserTestDefinition] | None = None,
        journey_suite: ValidatedBrowserJourneySuite | None = None,
        strict: bool = True,
        discovered_at: datetime | None = None,
    ) -> UnifiedTestInventory:
        """Compile a normalized, queryable, authoritative test inventory across all tiers.
        
        Args:
            project_id: Target project UUID or string.
            files_map: Optional source code files map for unit test discovery.
            ai_test_suite: Optional validated AI test suite.
            smoke_tests: Optional browser smoke test definitions.
            journey_suite: Optional validated browser journey suite.
            strict: If True, duplicate test_id collisions raise UnifiedTestInventoryConflictError.
                    If False, conflicts are recorded in inventory.conflicts without overwriting.
                    
        Returns:
            UnifiedTestInventory: Complete normalized catalog with bidirectional indexes.
        """
        clean_proj = str(project_id).strip().lower()

        raw_definitions: list[UnifiedTestDefinition] = []

        # 1. Discover Unit Tests
        if files_map:
            discovered_units = self.discover_unit_tests(clean_proj, files_map)
            raw_definitions.extend(discovered_units)

        # 2. Normalize AI Tests
        if ai_test_suite:
            discovered_ai = self.normalize_ai_tests(clean_proj, ai_test_suite)
            raw_definitions.extend(discovered_ai)

        # 3. Normalize Browser Smoke Tests
        if smoke_tests:
            discovered_smoke = self.normalize_browser_smoke_tests(clean_proj, smoke_tests)
            raw_definitions.extend(discovered_smoke)

        # 4. Normalize Browser Journeys
        if journey_suite:
            discovered_journeys = self.normalize_browser_journeys(clean_proj, journey_suite)
            raw_definitions.extend(discovered_journeys)

        # 5. Deduplication and Collision Detection
        tests_by_id: dict[str, UnifiedTestDefinition] = {}
        conflicts: list[TestInventoryConflict] = []
        ordered_tests: list[UnifiedTestDefinition] = []

        for item in raw_definitions:
            if item.test_id in tests_by_id:
                existing = tests_by_id[item.test_id]
                conflict_msg = (
                    f"Duplicate normalized test_id '{item.test_id}' collision between "
                    f"'{existing.source_reference}' ({existing.tier.value}) and "
                    f"'{item.source_reference}' ({item.tier.value})."
                )
                if strict:
                    raise UnifiedTestInventoryConflictError(conflict_msg)

                conflicts.append(
                    TestInventoryConflict(
                        test_id=item.test_id,
                        existing_source=existing.source_reference,
                        conflicting_source=item.source_reference,
                        message=conflict_msg,
                    )
                )
                logger.warning(conflict_msg)
            else:
                tests_by_id[item.test_id] = item
                ordered_tests.append(item)

        # Determine discovery completeness status
        if conflicts:
            discovery_status = DiscoveryStatus.CONFLICT
        else:
            discovery_status = DiscoveryStatus.COMPLETE

        # 6. Build Bidirectional Indexes
        tests_by_tier: dict[str, list[str]] = {tier.value: [] for tier in TestTier}
        tests_by_requirement: dict[str, list[str]] = {}
        requirements_by_test: dict[str, list[str]] = {}
        tier_counts: dict[str, int] = {tier.value: 0 for tier in TestTier}

        for test in ordered_tests:
            tier_key = test.tier.value
            tests_by_tier[tier_key].append(test.test_id)
            tier_counts[tier_key] += 1

            # Forward traceability index: test_id -> requirement_ids
            requirements_by_test[test.test_id] = list(test.requirement_links)

            # Reverse traceability index: requirement_id -> test_ids
            for req_id in test.requirement_links:
                clean_req = str(req_id).strip()
                if clean_req not in tests_by_requirement:
                    tests_by_requirement[clean_req] = []
                if test.test_id not in tests_by_requirement[clean_req]:
                    tests_by_requirement[clean_req].append(test.test_id)

        # Sort all indexed lists deterministically
        for req_id in tests_by_requirement:
            tests_by_requirement[req_id].sort()
        for tier_key in tests_by_tier:
            tests_by_tier[tier_key].sort()

        # Compute deterministic inventory ID
        all_test_ids = [t.test_id for t in ordered_tests]
        inventory_id = compute_deterministic_inventory_id(clean_proj, all_test_ids)

        inv_kwargs: dict[str, Any] = {
            "inventory_id": inventory_id,
            "project_id": clean_proj,
            "tests": ordered_tests,
            "discovery_status": discovery_status,
            "conflicts": conflicts,
            "tests_by_id": tests_by_id,
            "tests_by_tier": tests_by_tier,
            "tests_by_requirement": tests_by_requirement,
            "requirements_by_test": requirements_by_test,
            "tier_counts": tier_counts,
            "total_tests": len(ordered_tests),
            "metadata": {
                "discovered_tiers": [k for k, v in tier_counts.items() if v > 0],
                "conflict_count": len(conflicts),
            },
        }
        if discovered_at is not None:
            inv_kwargs["discovered_at"] = discovered_at

        return UnifiedTestInventory(**inv_kwargs)

    # ==========================================================================
    # 3. Internal Heuristics (Deterministic Mapping Only)
    # ==========================================================================

    def _infer_target_file(self, test_file_path: str, files_map: dict[str, str]) -> str | None:
        """Deterministically infer likely source file under test from conventional test paths.
        
        Example:
            'tests/test_calculator.py' -> 'app/calculator.py' or 'src/calculator.py'
        """
        filename = test_file_path.split("/")[-1]
        base_name = filename
        if base_name.startswith("test_"):
            base_name = base_name[5:]
        elif base_name.endswith("_test.py"):
            base_name = base_name[:-8] + ".py"

        # Check for candidate source files in files_map matching base_name
        candidates = [
            f for f in files_map
            if f.endswith(base_name) and not self.test_discovery.is_test_file(f)
        ]
        if candidates:
            return sorted(candidates)[0]
        return None
