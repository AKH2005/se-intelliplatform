"""Browser Journey Adapter (Phase 11K - Stage 3).

Translates authoritatively validated browser user journeys (ValidatedBrowserJourneySuite)
into Phase 11J deterministic browser test definitions (DeterministicBrowserTestDefinition)
for execution through the existing Playwright browser container testing infrastructure.

Key Invariants:
1. ONLY ValidatedBrowserJourneySuite is accepted; unvalidated candidate suites are rejected.
2. ZERO raw Playwright, Python, or JavaScript code is generated.
3. ZERO dynamic code evaluation (no eval, no exec).
4. ZERO shell execution, ZERO Docker execution within the adapter.
5. Deterministic test IDs derived strictly from journey identities without randomness or timestamps.
6. Complete requirement traceability preserved in test metadata.
7. Strict selector, route, and target parameter safety enforcement.
"""

import re
from typing import Any

from app.agents.browser_journey.contracts import (
    BrowserActionType,
    BrowserJourneyStep,
    BrowserTarget,
    BrowserTargetType,
)
from app.browser.contracts import (
    BrowserInteractionType,
    DeterministicBrowserTestDefinition,
    DeterministicInteraction,
)
from app.browser.journey.contracts import (
    ValidatedBrowserJourney,
    ValidatedBrowserJourneySuite,
)
from app.browser.journey.errors import BrowserJourneyAdaptationError


class BrowserJourneyAdapter:
    """Deterministic adapter converting ValidatedBrowserJourneySuite to Phase 11J test definitions."""

    @classmethod
    def target_to_selector(cls, target: BrowserTarget | None) -> str:
        """Deterministically map a BrowserTarget into a safe selector string.

        Args:
            target: The BrowserTarget element specification.

        Returns:
            str: Deterministic CSS or text selector for the target element.

        Raises:
            BrowserJourneyAdaptationError: If target is missing, invalid, or violates safety bounds.
        """
        if target is None:
            raise BrowserJourneyAdaptationError("Target element is required but was None.")

        target_type = target.target_type
        val = target.value.strip()

        if not val:
            raise BrowserJourneyAdaptationError("Target selector value cannot be empty.")

        # Defensive safety check on target value
        if any(bad in val.lower() for bad in ("<script", "javascript:", "data:", "eval(", "document.", "onload=")):
            raise BrowserJourneyAdaptationError(f"Target value contains prohibited injection tokens: '{val}'")

        if target_type == BrowserTargetType.TEST_ID:
            if '"' in val or '\\' in val:
                raise BrowserJourneyAdaptationError(f"TEST_ID target value cannot contain quotes or backslashes: '{val}'")
            return f'[data-testid="{val}"]'

        elif target_type == BrowserTargetType.ROLE:
            if '"' in val or '\\' in val:
                raise BrowserJourneyAdaptationError(f"ROLE target value cannot contain quotes or backslashes: '{val}'")
            return f'[role="{val}"]'

        elif target_type == BrowserTargetType.LABEL:
            if '"' in val or '\\' in val:
                raise BrowserJourneyAdaptationError(f"LABEL target value cannot contain quotes or backslashes: '{val}'")
            return f'[aria-label="{val}"], label:has-text("{val}")'

        elif target_type == BrowserTargetType.NAME:
            if '"' in val or '\\' in val:
                raise BrowserJourneyAdaptationError(f"NAME target value cannot contain quotes or backslashes: '{val}'")
            return f'[name="{val}"]'

        elif target_type == BrowserTargetType.TEXT:
            if '"' in val or '\\' in val:
                raise BrowserJourneyAdaptationError(f"TEXT target value cannot contain quotes or backslashes: '{val}'")
            return f'text="{val}"'

        elif target_type == BrowserTargetType.CSS_SELECTOR:
            DeterministicInteraction.validate_selector_safety(val)
            return val

        else:
            raise BrowserJourneyAdaptationError(f"Unsupported target type: {target_type}")

    @classmethod
    def step_to_interaction(cls, step: BrowserJourneyStep) -> DeterministicInteraction:
        """Translate a single BrowserJourneyStep into a DeterministicInteraction.

        Args:
            step: Validated journey step.

        Returns:
            DeterministicInteraction: Translated interaction specification.

        Raises:
            TypeError: If step is not a BrowserJourneyStep.
            BrowserJourneyAdaptationError: If step validation fails.
        """
        if not isinstance(step, BrowserJourneyStep):
            raise TypeError(f"Expected BrowserJourneyStep, got {type(step).__name__}")

        action = step.action
        timeout = min(max(float(step.timeout_seconds), 0.5), 15.0)

        if action == BrowserActionType.NAVIGATE:
            route = (step.route or "/").strip()
            if any(p in route.lower() for p in ("://", "javascript:", "data:", "file:", "about:", "blob:")):
                raise BrowserJourneyAdaptationError(f"Unsafe or external navigation route: '{route}'")
            if ".." in route:
                raise BrowserJourneyAdaptationError(f"Path traversal prohibited in navigation route: '{route}'")
            if not route.startswith("/"):
                route = "/" + route
            return DeterministicInteraction(
                action=BrowserInteractionType.NAVIGATE,
                selector="body",
                value=route,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.CLICK:
            if not step.target:
                raise BrowserJourneyAdaptationError(f"Step '{step.step_id}' ({action.value}) requires a target.")
            selector = cls.target_to_selector(step.target)
            return DeterministicInteraction(
                action=BrowserInteractionType.CLICK,
                selector=selector,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.FILL:
            if not step.target:
                raise BrowserJourneyAdaptationError(f"Step '{step.step_id}' ({action.value}) requires a target.")
            selector = cls.target_to_selector(step.target)
            return DeterministicInteraction(
                action=BrowserInteractionType.FILL,
                selector=selector,
                value=step.value or "",
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.SELECT:
            if not step.target:
                raise BrowserJourneyAdaptationError(f"Step '{step.step_id}' ({action.value}) requires a target.")
            selector = cls.target_to_selector(step.target)
            return DeterministicInteraction(
                action=BrowserInteractionType.SELECT,
                selector=selector,
                value=step.value or "",
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.CHECK:
            if not step.target:
                raise BrowserJourneyAdaptationError(f"Step '{step.step_id}' ({action.value}) requires a target.")
            selector = cls.target_to_selector(step.target)
            return DeterministicInteraction(
                action=BrowserInteractionType.CLICK,
                selector=selector,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.UNCHECK:
            if not step.target:
                raise BrowserJourneyAdaptationError(f"Step '{step.step_id}' ({action.value}) requires a target.")
            selector = cls.target_to_selector(step.target)
            return DeterministicInteraction(
                action=BrowserInteractionType.CLICK,
                selector=selector,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.SUBMIT:
            selector = (
                cls.target_to_selector(step.target)
                if step.target
                else 'button[type="submit"], input[type="submit"]'
            )
            return DeterministicInteraction(
                action=BrowserInteractionType.CLICK,
                selector=selector,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.ASSERT_TEXT:
            selector = cls.target_to_selector(step.target) if step.target else "body"
            expected_text = step.value or step.assertion or ""
            return DeterministicInteraction(
                action=BrowserInteractionType.ASSERT_TEXT,
                selector=selector,
                expected_text=expected_text,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.ASSERT_VISIBLE:
            selector = cls.target_to_selector(step.target) if step.target else "body"
            return DeterministicInteraction(
                action=BrowserInteractionType.ASSERT_VISIBLE,
                selector=selector,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.ASSERT_ELEMENT:
            selector = cls.target_to_selector(step.target) if step.target else "body"
            return DeterministicInteraction(
                action=BrowserInteractionType.ASSERT_VISIBLE,
                selector=selector,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.ASSERT_URL:
            expected_url = (step.route or step.value or step.assertion or "/").strip()
            if any(p in expected_url.lower() for p in ("://", "javascript:", "data:", "file:", "about:", "blob:")):
                raise BrowserJourneyAdaptationError(f"Unsafe external URL expectation: '{expected_url}'")
            return DeterministicInteraction(
                action=BrowserInteractionType.ASSERT_URL,
                selector="body",
                value=expected_url,
                timeout_seconds=timeout,
            )

        elif action == BrowserActionType.WAIT:
            wait_val = 1.0
            if step.value:
                try:
                    wait_val = float(step.value)
                except ValueError:
                    wait_val = step.timeout_seconds
            else:
                wait_val = step.timeout_seconds
            bounded_wait = min(max(wait_val, 0.1), 15.0)
            return DeterministicInteraction(
                action=BrowserInteractionType.WAIT,
                selector="body",
                value=str(bounded_wait),
                timeout_seconds=timeout,
            )

        else:
            raise BrowserJourneyAdaptationError(f"Unsupported BrowserActionType: {action}")

    @classmethod
    def adapt_journey(cls, journey: ValidatedBrowserJourney) -> DeterministicBrowserTestDefinition:
        """Translate a single ValidatedBrowserJourney into a DeterministicBrowserTestDefinition.

        Args:
            journey: A validated browser user journey.

        Returns:
            DeterministicBrowserTestDefinition: Deterministic test case definition.

        Raises:
            TypeError: If journey is not a ValidatedBrowserJourney.
            BrowserJourneyAdaptationError: If adaptation invariants are violated.
        """
        if not isinstance(journey, ValidatedBrowserJourney):
            raise TypeError(
                f"Expected ValidatedBrowserJourney, got {type(journey).__name__}"
            )

        # 1. Deterministic test_id derivation
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", journey.journey_id).strip("_")
        test_id = f"journey_{clean_id}"[:100]

        # 2. Determine initial target_path
        target_path = "/"
        if journey.steps and journey.steps[0].action == BrowserActionType.NAVIGATE and journey.steps[0].route:
            target_path = journey.steps[0].route
        elif journey.validated_target_routes:
            target_path = journey.validated_target_routes[0]

        # Defensive target_path check
        target_path = target_path.strip()
        if any(p in target_path.lower() for p in ("://", "javascript:", "data:", "file:", "about:", "blob:")):
            raise BrowserJourneyAdaptationError(
                f"Unsafe target_path for journey '{journey.journey_id}': '{target_path}'"
            )
        if ".." in target_path:
            raise BrowserJourneyAdaptationError(
                f"Path traversal in target_path for journey '{journey.journey_id}': '{target_path}'"
            )
        if not target_path.startswith("/"):
            target_path = "/" + target_path

        # 3. Translate all steps
        interactions = [cls.step_to_interaction(step) for step in journey.steps]

        # 4. Construct execution metadata for end-to-end traceability
        metadata: dict[str, Any] = {
            "journey_id": journey.journey_id,
            "title": journey.title,
            "category": journey.category.value if hasattr(journey.category, "value") else str(journey.category),
            "priority": journey.priority.value if hasattr(journey.priority, "value") else str(journey.priority),
            "requirement_ids": list(journey.validated_requirement_ids),
            "preconditions": list(journey.preconditions),
            "expected_outcomes": list(journey.expected_outcomes),
        }

        return DeterministicBrowserTestDefinition(
            test_id=test_id,
            name=journey.title[:200],
            target_path=target_path,
            expected_status=200,
            expected_title_contains=None,
            expected_elements=["body"],
            interactions=interactions,
            capture_screenshot=True,
            metadata=metadata,
        )

    @classmethod
    def adapt(
        cls,
        suite: ValidatedBrowserJourneySuite,
    ) -> list[DeterministicBrowserTestDefinition]:
        """Adapt a validated journey suite into a list of deterministic browser test definitions.

        Args:
            suite: An authoritatively validated browser journey suite.

        Returns:
            list[DeterministicBrowserTestDefinition]: Deterministic test definitions ready for BrowserTestingService.

        Raises:
            TypeError: If input is not a ValidatedBrowserJourneySuite (e.g. BrowserJourneySuiteCandidate).
            BrowserJourneyAdaptationError: If validation invariants are violated during adaptation.
        """
        if not isinstance(suite, ValidatedBrowserJourneySuite):
            raise TypeError(
                f"BrowserJourneyAdapter requires ValidatedBrowserJourneySuite, but received {type(suite).__name__}. "
                "Unvalidated candidate suites cannot be adapted for execution."
            )

        if not suite.journeys:
            raise BrowserJourneyAdaptationError("ValidatedBrowserJourneySuite must contain at least one journey.")

        return [cls.adapt_journey(journey) for journey in suite.journeys]
