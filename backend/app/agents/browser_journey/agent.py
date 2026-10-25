"""Browser Journey Generation Agent Implementation.

Phase 11K — Stage 1: BrowserJourneyGenerationAgent
Generates structured candidate browser user journeys (test intent) from bounded project context.

ARCHITECTURAL INVARIANTS:
1. Pure intent generation: Generates structured BrowserJourneySuiteCandidate ONLY.
2. ZERO execution authority: Does NOT execute tests, does NOT invoke Playwright,
   does NOT call Docker, does NOT touch the filesystem, and does NOT run shell commands.
3. Candidate output: Outputs are candidate proposals requiring subsequent Stage 2
   authoritative deterministic validation before adapter transformation or execution.
4. Single execution authority: Executed strictly through AgentExecutor governance.
"""

import logging
from typing import Any
from app.agents.base import AbstractBaseAgent
from app.agents.contracts import AgentMetadata, AgentType, ValidationResult
from app.agents.providers.base import AbstractLLMProvider, LLMMessage, LLMRequest
from app.agents.browser_journey.contracts import (
    BoundedRequirementInfo,
    BoundedRouteInfo,
    BrowserActionType,
    BrowserJourney,
    BrowserJourneyGenerationInput,
    BrowserJourneyStep,
    BrowserJourneySuiteCandidate,
    BrowserTarget,
    BrowserTargetType,
    JourneyCategory,
    JourneyPriority,
)
from app.agents.browser_journey.prompts import (
    SYSTEM_PROMPT,
    build_browser_journey_prompt,
)
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class BrowserJourneyGenerationAgent(AbstractBaseAgent[BrowserJourneySuiteCandidate]):
    """AI Agent responsible for generating bounded, structured browser user journeys.

    Identity:
    - agent_id: "browser-journey-generation"
    - version: "1.0.0"
    - category: GENERATION (AgentType.GENERATION)
    """

    __test__ = False

    def __init__(self) -> None:
        self._current_input: BrowserJourneyGenerationInput | None = None

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="browser-journey-generation",
            name="Browser Journey Generation Agent",
            description="Generates structured browser user journeys (test intent) targeting application web routes and active requirements.",
            version="1.0.0",
            agent_type=AgentType.GENERATION,
        )

    @property
    def output_schema(self) -> type[BrowserJourneySuiteCandidate]:
        return BrowserJourneySuiteCandidate

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        self._current_input = None

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Prepare bounded input context from project requirements and routes."""
        raw_input = (
            kwargs.get("browser_journey_input")
            or kwargs.get("journey_input")
            or kwargs.get("input")
        )

        if isinstance(raw_input, BrowserJourneyGenerationInput):
            journey_input = raw_input
        else:
            # Extract bounded requirements
            req_infos: list[BoundedRequirementInfo] = []
            if context.requirements:
                for r in context.requirements:
                    cat_val = None
                    if hasattr(r, "category") and r.category:
                        cat_val = r.category.value if hasattr(r.category, "value") else str(r.category)
                    req_infos.append(
                        BoundedRequirementInfo(
                            id=str(r.id),
                            title=getattr(r, "title", f"Requirement {r.id}"),
                            description=getattr(r, "description", "") or "",
                            category=cat_val,
                        )
                    )

            # Extract bounded routes
            raw_routes = kwargs.get("routes") or kwargs.get("discovered_routes") or []
            route_infos: list[BoundedRouteInfo] = []
            if isinstance(raw_routes, list):
                for item in raw_routes:
                    if isinstance(item, BoundedRouteInfo):
                        route_infos.append(item)
                    elif isinstance(item, dict):
                        route_infos.append(BoundedRouteInfo(**item))
                    elif isinstance(item, str):
                        clean_path = item if item.startswith("/") else f"/{item}"
                        route_infos.append(BoundedRouteInfo(path=clean_path, method="GET"))
            if not route_infos:
                route_infos.append(
                    BoundedRouteInfo(
                        path="/",
                        method="GET",
                        name="Root",
                        description="Default application root route",
                    )
                )

            # Extract architecture components
            arch_comps: list[str] = []
            arch_out = kwargs.get("architecture_recommendation")
            if arch_out and hasattr(arch_out, "components"):
                arch_comps = [c.name for c in arch_out.components if hasattr(c, "name")]
            elif isinstance(kwargs.get("architecture_components"), list):
                arch_comps = [str(c) for c in kwargs["architecture_components"]]

            # Extract file manifest
            manifest: list[str] = []
            if isinstance(kwargs.get("file_manifest"), list):
                manifest = [str(f) for f in kwargs["file_manifest"]]
            else:
                code_out = kwargs.get("code_generation") or kwargs.get("code_output")
                if hasattr(code_out, "generated_files") and isinstance(code_out.generated_files, list):
                    manifest = [f.path for f in code_out.generated_files if hasattr(f, "path")]

            allowed_cats = kwargs.get("target_categories") or list(JourneyCategory)

            journey_input = BrowserJourneyGenerationInput(
                project_id=context.project.id,
                project_name=getattr(context.project, "name", "Application Under Test"),
                development_version_id=kwargs.get("development_version_id"),
                version_number=kwargs.get("version_number"),
                requirements=req_infos,
                routes=route_infos,
                architecture_components=arch_comps,
                file_manifest=manifest,
                max_journeys=kwargs.get("max_journeys", 5),
                target_categories=allowed_cats,
            )

        self._current_input = journey_input
        return {"journey_input": journey_input}

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> BrowserJourneySuiteCandidate:
        """Lifecycle Hook 3: Invoke LLM provider to produce candidate journey suite."""
        journey_input: BrowserJourneyGenerationInput = analysis_result["journey_input"]
        user_prompt = build_browser_journey_prompt(journey_input)

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=provider.default_model,
            temperature=0.2,
            max_tokens=3000,
        )

        candidate = await provider.generate_structured(
            request=request,
            response_model=BrowserJourneySuiteCandidate,
        )

        if not candidate.journeys:
            candidate = self._synthesize_candidate_suite(journey_input)

        return candidate

    def _synthesize_candidate_suite(
        self,
        journey_input: BrowserJourneyGenerationInput,
    ) -> BrowserJourneySuiteCandidate:
        """Deterministically synthesize a valid candidate journey suite when LLM output is empty."""
        proj_name = journey_input.project_name or "Application Under Test"
        active_req_ids = [r.id for r in journey_input.requirements]
        journeys: list[BrowserJourney] = []

        routes = [r.path for r in journey_input.routes] if journey_input.routes else ["/"]
        primary_route = routes[0] if routes else "/"

        j1_reqs = active_req_ids[:1] if active_req_ids else []
        journeys.append(
            BrowserJourney(
                journey_id="BJ-001",
                title=f"Verify {proj_name[:40]} Web Application Root",
                description=f"Loads the primary web application root at '{primary_route}' and asserts document visibility.",
                category=JourneyCategory.HAPPY_PATH,
                priority=JourneyPriority.HIGH,
                requirement_ids=j1_reqs,
                target_routes=[primary_route],
                steps=[
                    BrowserJourneyStep(
                        step_id="step-1",
                        action=BrowserActionType.NAVIGATE,
                        route=primary_route,
                        description=f"Navigate to {primary_route}",
                    ),
                    BrowserJourneyStep(
                        step_id="step-2",
                        action=BrowserActionType.ASSERT_VISIBLE,
                        target=BrowserTarget(
                            target_type=BrowserTargetType.CSS_SELECTOR,
                            value="body",
                            description="Main document body container",
                        ),
                        description="Verify body is visible",
                    ),
                ],
                expected_outcomes=[f"Application renders document at {primary_route}"],
            )
        )

        additional_routes = [r for r in routes if r != primary_route]
        if additional_routes:
            sec_route = additional_routes[0]
            j2_reqs = active_req_ids[1:2] if len(active_req_ids) > 1 else j1_reqs
            journeys.append(
                BrowserJourney(
                    journey_id="BJ-002",
                    title=f"Verify {proj_name[:40]} Route {sec_route}",
                    description=f"Navigates to route '{sec_route}' and validates document availability.",
                    category=JourneyCategory.NAVIGATION,
                    priority=JourneyPriority.MEDIUM,
                    requirement_ids=j2_reqs,
                    target_routes=[sec_route],
                    steps=[
                        BrowserJourneyStep(
                            step_id="step-1",
                            action=BrowserActionType.NAVIGATE,
                            route=sec_route,
                            description=f"Navigate to {sec_route}",
                        ),
                        BrowserJourneyStep(
                            step_id="step-2",
                            action=BrowserActionType.ASSERT_VISIBLE,
                            target=BrowserTarget(
                                target_type=BrowserTargetType.CSS_SELECTOR,
                                value="body",
                                description="Document body container",
                            ),
                            description="Verify route document is visible",
                        ),
                    ],
                    expected_outcomes=[f"Route {sec_route} is accessible"],
                )
            )

        return BrowserJourneySuiteCandidate(
            suite_name=f"{proj_name} Browser Journey Suite",
            summary=f"Synthesized browser user journeys validating active requirements and routes for {proj_name}.",
            journeys=journeys[:journey_input.max_journeys],
            metadata={"synthesized": True},
        )

    def validate_output(
        self,
        output: BrowserJourneySuiteCandidate,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic Stage 1 candidate-schema validation.
        
        Enforces candidate-level structural invariants:
        - Output is a valid BrowserJourneySuiteCandidate
        - Journey IDs are unique
        - Each journey contains at least one step
        - Action-specific field completeness
        
        Note: Authoritative requirement coverage and route-manifest matching
        are explicitly deferred to Stage 2 deterministic validation.
        """
        if not isinstance(output, BrowserJourneySuiteCandidate):
            return ValidationResult(
                is_valid=False,
                errors=[f"Output must be a BrowserJourneySuiteCandidate, received '{type(output).__name__}'."],
            )

        errors: list[str] = []
        journey_ids: set[str] = set()

        for j_idx, journey in enumerate(output.journeys):
            if not isinstance(journey, BrowserJourney):
                errors.append(f"Journey at index {j_idx} is not a BrowserJourney instance.")
                continue

            if journey.journey_id in journey_ids:
                errors.append(f"Duplicate journey_id '{journey.journey_id}' detected at index {j_idx}.")
            journey_ids.add(journey.journey_id)

            if not journey.steps:
                errors.append(f"Journey '{journey.journey_id}' contains no steps.")

            step_ids: set[str] = set()
            for s_idx, step in enumerate(journey.steps):
                if step.step_id in step_ids:
                    errors.append(f"Journey '{journey.journey_id}' has duplicate step_id '{step.step_id}'.")
                step_ids.add(step.step_id)

                # Validate action completeness
                if step.action == BrowserActionType.NAVIGATE and not step.route:
                    errors.append(f"Step '{step.step_id}' (NAVIGATE) missing required 'route'.")
                elif step.action in (BrowserActionType.CLICK, BrowserActionType.CHECK, BrowserActionType.UNCHECK, BrowserActionType.SUBMIT) and not step.target:
                    errors.append(f"Step '{step.step_id}' ({step.action.value}) missing required 'target'.")
                elif step.action in (BrowserActionType.FILL, BrowserActionType.SELECT):
                    if not step.target:
                        errors.append(f"Step '{step.step_id}' ({step.action.value}) missing required 'target'.")
                    if step.value is None:
                        errors.append(f"Step '{step.step_id}' ({step.action.value}) missing required 'value'.")
                elif step.action == BrowserActionType.ASSERT_TEXT:
                    if not step.target:
                        errors.append(f"Step '{step.step_id}' (ASSERT_TEXT) missing required 'target'.")
                    if step.value is None and step.assertion is None:
                        errors.append(f"Step '{step.step_id}' (ASSERT_TEXT) requires either 'value' or 'assertion'.")

        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        return ValidationResult(is_valid=True)
