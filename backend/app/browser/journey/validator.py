"""Deterministic Authoritative Validator for Browser Journey Candidates.

Phase 11K — Stage 2: Browser Journey Validator
Transforms BrowserJourneySuiteCandidate into ValidatedBrowserJourneySuite
under strict deterministic backend rules, zero execution, and no LLMs.

ARCHITECTURAL INVARIANTS:
1. Pure Deterministic Validation: AI proposes; backend validates. No LLM fallback, no guessing.
2. Complete Isolation: Verifies project isolation. Cross-project requirement references are rejected.
3. Authoritative Route Verification: Validates routes against the application route manifest,
   including deterministic parameterized path templates (e.g. '/projects/{id}').
4. Comprehensive Security Sniffing: Prohibits raw Playwright snippets, dangerous schemes,
   shell/Docker commands, and credentials.
5. Strict Complexity Caps: Enforces journey count, step limits, and string bounds.
"""

import logging
import re
from typing import Sequence
from app.agents.browser_journey.contracts import (
    BrowserActionType,
    BrowserJourney,
    BrowserJourneyStep,
    BrowserJourneySuiteCandidate,
    BrowserTarget,
    BrowserTargetType,
    MAX_DESCRIPTION_LENGTH,
    MAX_JOURNEY_ID_LENGTH,
    MAX_JOURNEYS_PER_SUITE,
    MAX_ROUTE_LENGTH,
    MAX_STEP_ID_LENGTH,
    MAX_STEPS_PER_JOURNEY,
    MAX_TITLE_LENGTH,
    MAX_VALUE_LENGTH,
    RE_DANGEROUS_COMMANDS,
    RE_DANGEROUS_SCHEMES,
    RE_EXTERNAL_URL,
    RE_RAW_PLAYWRIGHT,
    RE_SCRIPT_INJECTION,
    RE_SECRET_PATTERNS,
)
from app.browser.journey.contracts import (
    MAX_ASSERTION_LENGTH,
    MAX_CSS_SELECTOR_LENGTH,
    MAX_EXPECTED_OUTCOME_LENGTH,
    MAX_PRECONDITION_LENGTH,
    MAX_TOTAL_STEPS_PER_SUITE,
    MAX_WAIT_SECONDS,
    MIN_WAIT_SECONDS,
    ValidatedBrowserJourney,
    ValidatedBrowserJourneySuite,
    ValidationCategory,
    ValidationContext,
    ValidationIssue,
    ValidationOutcome,
    ValidationSeverity,
)
from app.browser.journey.coverage import RequirementCoverageEngine
from app.browser.journey.errors import BrowserJourneyValidationError

logger = logging.getLogger(__name__)


class BrowserJourneyValidator:
    """Authoritative deterministic validation engine for AI-generated browser journeys."""

    @classmethod
    def validate(
        cls,
        candidate: BrowserJourneySuiteCandidate,
        context: ValidationContext,
    ) -> tuple[ValidatedBrowserJourneySuite | None, ValidationOutcome]:
        """Validate candidate suite against authoritative project context and route manifest.
        
        Returns:
            Tuple of (ValidatedBrowserJourneySuite if valid else None, ValidationOutcome).
        """
        issues: list[ValidationIssue] = []

        # 1. Suite-Level Complexity & Structure
        cls._validate_suite_structure_and_limits(candidate, issues)

        # 2. Compile Authoritative Route Patterns
        compiled_routes = cls._compile_authoritative_routes(context.authoritative_routes)

        # 3. Track Suite-Level Uniqueness
        seen_journey_ids: set[str] = set()
        seen_signatures: dict[tuple, str] = {}
        validated_journeys: list[ValidatedBrowserJourney] = []

        total_steps_count = sum(len(j.steps) for j in candidate.journeys)
        if total_steps_count > MAX_TOTAL_STEPS_PER_SUITE:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    message=(
                        f"Candidate suite exceeds total steps limit of {MAX_TOTAL_STEPS_PER_SUITE} "
                        f"(contains {total_steps_count} steps across all journeys)."
                    ),
                )
            )

        # 4. Individual Journey Validation
        for journey in candidate.journeys:
            journey_issues = cls._validate_journey(
                journey=journey,
                context=context,
                compiled_routes=compiled_routes,
                seen_journey_ids=seen_journey_ids,
                seen_signatures=seen_signatures,
            )
            issues.extend(journey_issues)

            # If no errors on this journey, construct ValidatedBrowserJourney
            journey_errors = [i for i in journey_issues if i.severity == ValidationSeverity.ERROR]
            if not journey_errors:
                # Filter validated requirement IDs and target routes
                val_reqs = sorted(
                    list({r for r in journey.requirement_ids if r in context.active_requirement_ids})
                )
                val_routes = sorted(list(set(journey.target_routes)))
                validated_journeys.append(
                    ValidatedBrowserJourney(
                        journey_id=journey.journey_id,
                        title=journey.title,
                        description=journey.description,
                        category=journey.category,
                        priority=journey.priority,
                        validated_requirement_ids=val_reqs,
                        preconditions=journey.preconditions,
                        validated_target_routes=val_routes,
                        steps=journey.steps,
                        expected_outcomes=journey.expected_outcomes,
                    )
                )

        # Determine overall validity
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        outcome = ValidationOutcome(
            is_valid=not has_errors,
            issues=issues,
        )

        if has_errors or not validated_journeys:
            return None, outcome

        # 5. Deterministic Coverage Calculation
        coverage_report = RequirementCoverageEngine.compute_coverage(
            validated_journeys=validated_journeys,
            active_requirement_ids=context.active_requirement_ids,
        )

        # 6. Build Validated Suite
        validated_suite = ValidatedBrowserJourneySuite(
            project_id=context.project_id,
            suite_name=candidate.suite_name,
            summary=candidate.summary,
            journeys=validated_journeys,
            coverage_report=coverage_report,
            metadata=candidate.metadata,
        )

        return validated_suite, outcome

    @classmethod
    def validate_or_raise(
        cls,
        candidate: BrowserJourneySuiteCandidate,
        context: ValidationContext,
    ) -> ValidatedBrowserJourneySuite:
        """Validate candidate suite and raise BrowserJourneyValidationError on failure."""
        suite, outcome = cls.validate(candidate, context)
        if not outcome.is_valid or suite is None:
            raise BrowserJourneyValidationError(
                message="Browser journey candidate suite failed deterministic validation.",
                outcome=outcome,
            )
        return suite

    # ==========================================================================
    # Internal Validation Helpers
    # ==========================================================================

    @classmethod
    def _validate_suite_structure_and_limits(
        cls,
        candidate: BrowserJourneySuiteCandidate,
        issues: list[ValidationIssue],
    ) -> None:
        """Check top-level candidate suite structural completeness and bounds."""
        if not candidate.journeys:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.STRUCTURE,
                    code="EMPTY_SUITE",
                    message="Candidate journey suite contains no journeys.",
                )
            )

        if len(candidate.journeys) > MAX_JOURNEYS_PER_SUITE:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    message=(
                        f"Candidate suite exceeds journey limit of {MAX_JOURNEYS_PER_SUITE} "
                        f"(contains {len(candidate.journeys)} journeys)."
                    ),
                )
            )

    @classmethod
    def _validate_journey(
        cls,
        journey: BrowserJourney,
        context: ValidationContext,
        compiled_routes: list[tuple[str, re.Pattern[str]]],
        seen_journey_ids: set[str],
        seen_signatures: dict[tuple, str],
    ) -> list[ValidationIssue]:
        """Validate an individual journey against structural, requirement, route, and security rules."""
        issues: list[ValidationIssue] = []
        j_id = journey.journey_id

        # Journey ID checks
        if len(j_id) > MAX_JOURNEY_ID_LENGTH:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    journey_id=j_id,
                    field="journey_id",
                    message=f"Journey ID '{j_id}' exceeds maximum length of {MAX_JOURNEY_ID_LENGTH}.",
                )
            )

        if j_id in seen_journey_ids:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.DUPLICATE,
                    code="DUPLICATE_JOURNEY_ID",
                    journey_id=j_id,
                    field="journey_id",
                    message=f"Duplicate journey_id '{j_id}' detected in candidate suite.",
                )
            )
        seen_journey_ids.add(j_id)

        # Check duplicate journey content
        sig = cls._compute_journey_signature(journey)
        if sig in seen_signatures:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.DUPLICATE,
                    code="DUPLICATE_JOURNEY_CONTENT",
                    journey_id=j_id,
                    message=(
                        f"Journey '{j_id}' has identical title, category, and interaction sequence "
                        f"to journey '{seen_signatures[sig]}'."
                    ),
                )
            )
        else:
            seen_signatures[sig] = j_id

        # Text length & security checks
        if len(journey.title) > MAX_TITLE_LENGTH:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    journey_id=j_id,
                    field="title",
                    message=f"Journey title exceeds limit of {MAX_TITLE_LENGTH} characters.",
                )
            )
        cls._sniff_security_issues(journey.title, "title", j_id, None, issues)

        if len(journey.description) > MAX_DESCRIPTION_LENGTH:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    journey_id=j_id,
                    field="description",
                    message=f"Journey description exceeds limit of {MAX_DESCRIPTION_LENGTH} characters.",
                )
            )
        cls._sniff_security_issues(journey.description, "description", j_id, None, issues)

        # Preconditions & Outcomes
        for idx, prec in enumerate(journey.preconditions):
            if len(prec) > MAX_PRECONDITION_LENGTH:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.COMPLEXITY,
                        code="COMPLEXITY_LIMIT_EXCEEDED",
                        journey_id=j_id,
                        field=f"preconditions[{idx}]",
                        message=f"Precondition item exceeds limit of {MAX_PRECONDITION_LENGTH} characters.",
                    )
                )
            cls._sniff_security_issues(prec, f"preconditions[{idx}]", j_id, None, issues)

        for idx, outc in enumerate(journey.expected_outcomes):
            if len(outc) > MAX_EXPECTED_OUTCOME_LENGTH:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.COMPLEXITY,
                        code="COMPLEXITY_LIMIT_EXCEEDED",
                        journey_id=j_id,
                        field=f"expected_outcomes[{idx}]",
                        message=f"Expected outcome item exceeds limit of {MAX_EXPECTED_OUTCOME_LENGTH} characters.",
                    )
                )
            cls._sniff_security_issues(outc, f"expected_outcomes[{idx}]", j_id, None, issues)

        # Requirement validation
        cls._validate_requirements(journey, context, issues)

        # Target routes validation
        for r_idx, route in enumerate(journey.target_routes):
            cls._validate_single_route(route, compiled_routes, j_id, None, f"target_routes[{r_idx}]", issues)

        # Steps validation
        if not journey.steps:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.STRUCTURE,
                    code="EMPTY_STEPS",
                    journey_id=j_id,
                    field="steps",
                    message=f"Journey '{j_id}' contains no interaction steps.",
                )
            )

        if len(journey.steps) > MAX_STEPS_PER_JOURNEY:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    journey_id=j_id,
                    field="steps",
                    message=f"Journey '{j_id}' exceeds maximum step limit of {MAX_STEPS_PER_JOURNEY} (contains {len(journey.steps)} steps).",
                )
            )

        seen_step_ids: set[str] = set()
        for step in journey.steps:
            cls._validate_step(step, compiled_routes, j_id, seen_step_ids, issues)

        return issues

    @classmethod
    def _validate_requirements(
        cls,
        journey: BrowserJourney,
        context: ValidationContext,
        issues: list[ValidationIssue],
    ) -> None:
        """Deterministically validate requirement IDs for existence, project isolation, and active status."""
        j_id = journey.journey_id

        for req_id in journey.requirement_ids:
            clean_id = req_id.strip()

            # 1. Project isolation check: does ID belong to another project?
            if clean_id in context.other_project_requirement_ids:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.REQUIREMENT,
                        code="CROSS_PROJECT_REQUIREMENT_FORBIDDEN",
                        journey_id=j_id,
                        field="requirement_ids",
                        message=(
                            f"Requirement '{clean_id}' belongs to another project. "
                            "Cross-project requirement references violate platform isolation."
                        ),
                    )
                )
                continue

            # 2. Check if ID exists in the target project
            exists_in_project = (
                clean_id in context.all_project_requirement_ids
                or clean_id in context.active_requirement_ids
            )
            if not exists_in_project:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.REQUIREMENT,
                        code="HALLUCINATED_REQUIREMENT",
                        journey_id=j_id,
                        field="requirement_ids",
                        message=(
                            f"Requirement '{clean_id}' does not exist in project '{context.project_id}'. "
                            "Hallucinated requirement references are strictly rejected."
                        ),
                    )
                )
                continue

            # 3. Check if requirement is active
            if clean_id not in context.active_requirement_ids:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.REQUIREMENT,
                        code="INACTIVE_REQUIREMENT",
                        journey_id=j_id,
                        field="requirement_ids",
                        message=(
                            f"Requirement '{clean_id}' is recorded in the project but is inactive, "
                            "deferred, rejected, or archived. Only active requirements can be tested."
                        ),
                    )
                )

    @classmethod
    def _validate_step(
        cls,
        step: BrowserJourneyStep,
        compiled_routes: list[tuple[str, re.Pattern[str]]],
        journey_id: str,
        seen_step_ids: set[str],
        issues: list[ValidationIssue],
    ) -> None:
        """Validate step-level action semantics, target bounds, routes, and security."""
        s_id = step.step_id

        # Step ID checks
        if len(s_id) > MAX_STEP_ID_LENGTH:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    journey_id=journey_id,
                    step_id=s_id,
                    field="step_id",
                    message=f"Step ID '{s_id}' exceeds maximum length of {MAX_STEP_ID_LENGTH}.",
                )
            )

        if s_id in seen_step_ids:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.DUPLICATE,
                    code="DUPLICATE_STEP_ID",
                    journey_id=journey_id,
                    step_id=s_id,
                    field="step_id",
                    message=f"Duplicate step_id '{s_id}' within journey '{journey_id}'.",
                )
            )
        seen_step_ids.add(s_id)

        # Description check
        cls._sniff_security_issues(step.description, "description", journey_id, s_id, issues)

        # Action semantics validation
        action = step.action

        if action == BrowserActionType.NAVIGATE:
            if not step.route:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACTION,
                        code="MISSING_ROUTE",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="route",
                        message=f"NAVIGATE step '{s_id}' requires a valid relative route.",
                    )
                )
            else:
                cls._validate_single_route(step.route, compiled_routes, journey_id, s_id, "route", issues)

        elif action in (
            BrowserActionType.CLICK,
            BrowserActionType.CHECK,
            BrowserActionType.UNCHECK,
            BrowserActionType.SUBMIT,
        ):
            if not step.target:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACTION,
                        code="MISSING_TARGET",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="target",
                        message=f"{action.value} step '{s_id}' requires a target element.",
                    )
                )

        elif action in (BrowserActionType.FILL, BrowserActionType.SELECT):
            if not step.target:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACTION,
                        code="MISSING_TARGET",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="target",
                        message=f"{action.value} step '{s_id}' requires a target element.",
                    )
                )
            if step.value is None:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACTION,
                        code="MISSING_VALUE",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="value",
                        message=f"{action.value} step '{s_id}' requires a value.",
                    )
                )

        elif action == BrowserActionType.ASSERT_TEXT:
            if not step.target:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACTION,
                        code="MISSING_TARGET",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="target",
                        message=f"ASSERT_TEXT step '{s_id}' requires a target element.",
                    )
                )
            if step.value is None and step.assertion is None:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACTION,
                        code="MISSING_ASSERTION",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="value",
                        message=f"ASSERT_TEXT step '{s_id}' requires either 'value' or 'assertion' to verify text.",
                    )
                )

        elif action in (BrowserActionType.ASSERT_VISIBLE, BrowserActionType.ASSERT_ELEMENT):
            if not step.target:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACTION,
                        code="MISSING_TARGET",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="target",
                        message=f"{action.value} step '{s_id}' requires a target element.",
                    )
                )

        elif action == BrowserActionType.ASSERT_URL:
            if not step.route and not step.value:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.ACTION,
                        code="MISSING_URL_ASSERTION",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="route",
                        message=f"ASSERT_URL step '{s_id}' requires 'route' or 'value' for expected URL pattern.",
                    )
                )
            if step.route:
                cls._validate_single_route(step.route, compiled_routes, journey_id, s_id, "route", issues)

        elif action == BrowserActionType.WAIT:
            if step.timeout_seconds < MIN_WAIT_SECONDS or step.timeout_seconds > MAX_WAIT_SECONDS:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.COMPLEXITY,
                        code="COMPLEXITY_LIMIT_EXCEEDED",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="timeout_seconds",
                        message=(
                            f"WAIT step '{s_id}' duration of {step.timeout_seconds}s exceeds bounds "
                            f"({MIN_WAIT_SECONDS}s - {MAX_WAIT_SECONDS}s)."
                        ),
                    )
                )

        # Validate target element if present
        if step.target:
            cls._validate_target(step.target, journey_id, s_id, issues)

        # Validate value if present
        if step.value is not None:
            cls._validate_step_value(step.value, journey_id, s_id, issues)

        # Validate assertion if present
        if step.assertion:
            if len(step.assertion) > MAX_ASSERTION_LENGTH:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.COMPLEXITY,
                        code="COMPLEXITY_LIMIT_EXCEEDED",
                        journey_id=journey_id,
                        step_id=s_id,
                        field="assertion",
                        message=f"Assertion string in step '{s_id}' exceeds limit of {MAX_ASSERTION_LENGTH}.",
                    )
                )
            cls._sniff_security_issues(step.assertion, "assertion", journey_id, s_id, issues)

    @classmethod
    def _validate_target(
        cls,
        target: BrowserTarget,
        journey_id: str,
        step_id: str,
        issues: list[ValidationIssue],
    ) -> None:
        """Validate target element selector correctness, safety, and complexity."""
        val = target.value

        if len(val) > MAX_VALUE_LENGTH:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    journey_id=journey_id,
                    step_id=step_id,
                    field="target.value",
                    message=f"Target selector value in step '{step_id}' exceeds limit of {MAX_VALUE_LENGTH}.",
                )
            )

        # Security check on target value
        cls._sniff_security_issues(val, "target.value", journey_id, step_id, issues)

        # CSS_SELECTOR specific safety check
        if target.target_type == BrowserTargetType.CSS_SELECTOR:
            css_err = cls._validate_css_selector(val)
            if css_err:
                issues.append(
                    ValidationIssue(
                        category=ValidationCategory.TARGET,
                        code="DANGEROUS_CSS_SELECTOR",
                        journey_id=journey_id,
                        step_id=step_id,
                        field="target.value",
                        message=f"Invalid CSS selector in step '{step_id}': {css_err}",
                    )
                )

    @classmethod
    def _validate_step_value(
        cls,
        value: str,
        journey_id: str,
        step_id: str,
        issues: list[ValidationIssue],
    ) -> None:
        """Validate test data fill/assertion value against secrets and bounds."""
        if len(value) > MAX_VALUE_LENGTH:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    journey_id=journey_id,
                    step_id=step_id,
                    field="value",
                    message=f"Step value in step '{step_id}' exceeds limit of {MAX_VALUE_LENGTH}.",
                )
            )

        # Check for control characters (e.g. null bytes)
        if "\x00" in value:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    code="UNSAFE_FILL_VALUE",
                    journey_id=journey_id,
                    step_id=step_id,
                    field="value",
                    message=f"Step '{step_id}' value contains forbidden null byte control characters.",
                )
            )

        # Sniff general security issues (scripts, commands, secrets)
        cls._sniff_security_issues(value, "value", journey_id, step_id, issues)

    @classmethod
    def _validate_single_route(
        cls,
        route: str,
        compiled_routes: list[tuple[str, re.Pattern[str]]],
        journey_id: str,
        step_id: str | None,
        field_name: str,
        issues: list[ValidationIssue],
    ) -> None:
        """Validate single route for security and authoritative route manifest matching."""
        clean = route.strip()

        if len(clean) > MAX_ROUTE_LENGTH:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.COMPLEXITY,
                    code="COMPLEXITY_LIMIT_EXCEEDED",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=f"Route '{clean}' exceeds maximum length of {MAX_ROUTE_LENGTH}.",
                )
            )

        # Security check: dangerous schemes
        if RE_DANGEROUS_SCHEMES.search(clean):
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    code="UNSAFE_ROUTE_SCHEME",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=f"Prohibited dangerous URI scheme detected in route '{clean}'.",
                )
            )
            return

        # Security check: external URLs
        if RE_EXTERNAL_URL.search(clean):
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    code="EXTERNAL_URL_FORBIDDEN",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=f"External web URLs are prohibited in '{field_name}' ('{clean}').",
                )
            )
            return

        # Route must be relative starting with /
        if not clean.startswith("/"):
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.ROUTE,
                    code="INVALID_ROUTE_FORMAT",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=f"Application route must be relative and begin with '/' (received '{clean}').",
                )
            )
            return

        # Authoritative route manifest matching
        matched = False
        for raw_manifest_route, pattern in compiled_routes:
            if pattern.fullmatch(clean):
                matched = True
                break

        if not matched:
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.ROUTE,
                    code="NONEXISTENT_ROUTE",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=(
                        f"Route '{clean}' does not exist in the authoritative application route manifest. "
                        "Unmapped candidate routes are strictly rejected."
                    ),
                )
            )

    @classmethod
    def _compile_authoritative_routes(
        cls,
        manifest_routes: list[str],
    ) -> list[tuple[str, re.Pattern[str]]]:
        """Compile application route manifest paths into regex matchers supporting path templates."""
        compiled: list[tuple[str, re.Pattern[str]]] = []

        for r in manifest_routes:
            clean = r.strip()
            if not clean:
                continue

            # Escape regex characters
            escaped = re.escape(clean)

            # Replace escaped path parameters like \{project_id\} or \{id\} with [^/]+
            pattern_str = re.sub(r"\\\{[^}]+\\\}", r"[^/]+", escaped)

            # Allow optional trailing slash
            if pattern_str.endswith("/"):
                pattern_str = pattern_str[:-1] + "/?"
            elif pattern_str != "/":
                pattern_str = pattern_str + "/?"

            try:
                rx = re.compile(f"^{pattern_str}$")
                compiled.append((clean, rx))
            except re.error as re_err:
                logger.warning(f"Failed to compile route pattern for '{clean}': {re_err}")
                # Fallback to exact match pattern
                rx = re.compile(f"^{re.escape(clean)}/?$")
                compiled.append((clean, rx))

        # Always permit root route '/' if not already in manifest
        if not any(r == "/" for r, _ in compiled):
            compiled.append(("/", re.compile(r"^/?$")))

        return compiled

    @classmethod
    def _sniff_security_issues(
        cls,
        text: str | None,
        field_name: str,
        journey_id: str,
        step_id: str | None,
        issues: list[ValidationIssue],
    ) -> None:
        """Scan string content for Playwright code, command injection, scripts, and secrets."""
        if not text:
            return

        if RE_RAW_PLAYWRIGHT.search(text):
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    code="RAW_PLAYWRIGHT_CODE",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=f"Executable Playwright code detected in '{field_name}'.",
                )
            )

        if RE_DANGEROUS_COMMANDS.search(text):
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    code="DANGEROUS_COMMAND",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=f"Prohibited shell or Docker command detected in '{field_name}'.",
                )
            )

        if RE_SCRIPT_INJECTION.search(text):
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    code="SCRIPT_INJECTION",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=f"Prohibited script execution syntax detected in '{field_name}'.",
                )
            )

        if RE_SECRET_PATTERNS.search(text):
            issues.append(
                ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    code="UNSAFE_FILL_VALUE",
                    journey_id=journey_id,
                    step_id=step_id,
                    field=field_name,
                    message=f"Potential credential or secret pattern detected in '{field_name}'.",
                )
            )

    @classmethod
    def _validate_css_selector(cls, selector: str) -> str | None:
        """Validate CSS selector for length, injection safety, and balanced brackets."""
        if len(selector) > MAX_CSS_SELECTOR_LENGTH:
            return f"Selector exceeds length of {MAX_CSS_SELECTOR_LENGTH} characters."

        # Forbidden scripting / styling injection patterns
        if re.search(
            r"(?i)(<script|javascript:|eval\(|expression\(|-moz-binding|@import|url\(|document\.|window\.|Function\()",
            selector,
        ):
            return f"Prohibited injection pattern detected in CSS selector: '{selector}'."

        # Balanced brackets check
        stack: list[str] = []
        pairs = {")": "(", "]": "[", "}": "{"}
        for char in selector:
            if char in "([{":
                stack.append(char)
            elif char in ")]}":
                if not stack or stack[-1] != pairs[char]:
                    return f"Unbalanced brackets in CSS selector: '{selector}'."
                stack.pop()
        if stack:
            return f"Unbalanced brackets in CSS selector: '{selector}'."

        return None

    @classmethod
    def _compute_journey_signature(cls, journey: BrowserJourney) -> tuple:
        """Produce a deterministic signature for detecting identical duplicate journeys."""
        steps_sig = tuple(
            (
                s.action.value,
                s.route or "",
                s.target.target_type.value if s.target else "",
                s.target.value if s.target else "",
                s.value or "",
            )
            for s in journey.steps
        )
        return (
            journey.title.strip().lower(),
            journey.category.value,
            steps_sig,
        )
