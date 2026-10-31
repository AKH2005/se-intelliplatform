"""Comprehensive Intelligence, Reasoning, and Conversational Evaluation Suite.

Evaluates IntelliGuide and IntelliDev against Phase 3A requirements:
1. Source-code explanation grounded in retrieved files.
2. Missing-file requests truthfully stating file absence.
3. Live Preview and frontend/backend debugging grounded in runtime diagnostics.
4. Regression protection: Normal questions NEVER receive repeated static-analysis messages.
5. Verification troubleshooting explicitly requesting static analysis.
6. Ambiguous requirement handling with clarifying questions.
7. Conversational follow-up continuity and context preservation.
8. Multi-file feature planning without fast-path hijacking.
9. Provider timeout, rate-limit resilience, and safe error surfacing.
10. Cross-project data isolation and user authorization boundaries.
11. Truthful reporting: no fake test execution or unverified claims.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.exceptions import ProviderError, TransientProviderError
from app.agents.providers.mock import MockLLMProvider
from app.main import app
from app.api.dependencies import get_assistant_llm_provider
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.models.user import User
from app.schemas.assistant import (
    AssistantActionCandidate,
    AssistantContext,
    AssistantResponseSchema,
)
from app.services.assistant_context_builder import AssistantContextBuilder
from app.services.assistant_reasoning_service import AssistantReasoningService
from app.services.intent_router import AssistantIntent, IntentClassificationResult, IntentRouter


# -----------------------------------------------------------------------------
# 1. Source-Code Explanation Grounding
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_source_code_explanation():
    """Verify assistant explains components based strictly on retrieved files and suppresses actions."""
    mock_provider = MockLLMProvider()
    explanation_reply = AssistantResponseSchema(
        message=(
            "The main task manager component is defined in `frontend/src/App.tsx`. "
            "It manages `tasks` state via `useState<Task[]>([])` and `filter` state for 'ALL', 'PENDING', 'COMPLETED'. "
            "Task creation is handled in `handleCreateTask`, calling `taskApi.createTask`."
        ),
        suggested_action=None,
    )
    mock_provider.register_structured_response(explanation_reply)

    reasoning_svc = AssistantReasoningService(provider=mock_provider)
    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
        active_version_number=3,
        active_version_status="VERIFIED",
        retrieved_files=[
            {
                "path": "frontend/src/App.tsx",
                "language": "typescript",
                "size_bytes": 1024,
                "content": "export function App() { const [tasks, setTasks] = useState([]); }",
            }
        ],
    )

    query = "Explain how the React task manager in frontend/src/App.tsx works and its state management."
    classification = IntentRouter.classify(query)
    assert classification.intent == AssistantIntent.CODE_EXPLANATION
    assert classification.persona == "IntelliDev"

    result = await reasoning_svc.generate_response(
        user_message=query,
        context=context,
        classification=classification,
    )

    assert "frontend/src/App.tsx" in result.message
    assert "useState" in result.message
    assert result.suggested_action is None
    assert result.persona == "IntelliDev"
    assert result.intent == AssistantIntent.CODE_EXPLANATION.value


# -----------------------------------------------------------------------------
# 2. Missing-File Questions (Truthful Reporting)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_missing_file_truthful_reporting():
    """Verify assistant explicitly reports when a requested file is absent from active version."""
    mock_provider = MockLLMProvider()
    missing_file_reply = AssistantResponseSchema(
        message=(
            "The requested file `backend/auth_service.py` does not exist in the active version (v3). "
            "The active files in this project are: `backend/app/main.py`, `backend/app/api.py`, `frontend/src/App.tsx`."
        ),
        suggested_action=None,
    )
    mock_provider.register_structured_response(missing_file_reply)

    reasoning_svc = AssistantReasoningService(provider=mock_provider)
    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
        active_version_number=3,
        active_version_status="VERIFIED",
        missing_files_requested=["backend/auth_service.py"],
        files_manifest_summary=[
            {"path": "backend/app/main.py", "language": "python", "size_bytes": 500},
            {"path": "frontend/src/App.tsx", "language": "typescript", "size_bytes": 1200},
        ],
    )

    query = "Explain how authentication works in backend/auth_service.py."
    classification = IntentRouter.classify(query)
    assert classification.intent == AssistantIntent.CODE_EXPLANATION

    result = await reasoning_svc.generate_response(
        user_message=query,
        context=context,
        classification=classification,
    )

    assert "does not exist in the active version" in result.message
    assert result.suggested_action is None


# -----------------------------------------------------------------------------
# 3. Live Preview Debugging Grounded in Runtime Diagnostics
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_live_preview_debugging_diagnostics():
    """Verify assistant diagnoses preview discrepancies using preview runtime diagnostics."""
    mock_provider = MockLLMProvider()
    debug_reply = AssistantResponseSchema(
        message=(
            "Observed Symptom: Changes are not visible in Live Preview.\n"
            "Evidence: The Live Preview runtime is running on port 8001 in 'template' mode, serving a default prototype "
            "rather than custom version v3 code.\n"
            "Facts vs Hypotheses: It is confirmed that the preview server is active, but custom code synchronization has not run.\n"
            "Recommended Next Step: Rebuild or sync the active version to the preview container."
        ),
        suggested_action=None,
    )
    mock_provider.register_structured_response(debug_reply)

    reasoning_svc = AssistantReasoningService(provider=mock_provider)
    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
        active_version_number=3,
        active_version_status="FAILED_VERIFICATION",
        verification_summary="Verification failed with 1 issue(s): Missing mandatory static analysis report",
        preview_runtime_status="RUNNING",
        preview_runtime_mode="template",
        preview_runtime_port=8001,
        preview_diagnostics_summary="Preview runtime RUNNING on port 8001. (mode='template'; active project matched)",
    )

    query = "the changes are not seen in live preview"
    classification = IntentRouter.classify(query)
    assert classification.intent == AssistantIntent.DEBUGGING
    assert classification.diagnostic_focus == "preview_runtime"

    result = await reasoning_svc.generate_response(
        user_message=query,
        context=context,
        classification=classification,
    )

    assert "Live Preview runtime" in result.message
    assert result.suggested_action is None
    # Crucially, must not recommend static analysis when diagnosing preview state
    assert "static analysis" not in result.message.lower()


# -----------------------------------------------------------------------------
# 4. Regression Protection: Normal Questions NEVER Receive Static Analysis
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_anti_hijacking_regression_static_analysis():
    """Regression test: FAILED_VERIFICATION in context MUST NOT cause RUN_STATIC_ANALYSIS on normal questions."""
    mock_provider = MockLLMProvider()
    # Simulate a misaligned LLM that attempts to inject RUN_STATIC_ANALYSIS because context had failed verification
    hijacked_reply = AssistantResponseSchema(
        message="The active development version is marked as FAILED_VERIFICATION. Here is the App.tsx component explanation.",
        suggested_action=AssistantActionCandidate(
            action_id="RUN_STATIC_ANALYSIS",
            parameters={},
        ),
    )
    mock_provider.register_structured_response(hijacked_reply)

    reasoning_svc = AssistantReasoningService(provider=mock_provider)
    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
        active_version_number=3,
        active_version_status="FAILED_VERIFICATION",
        verification_summary="Verification failed with 1 issue(s): Missing mandatory static analysis report",
    )

    query = "Explain how the React task manager in frontend/src/App.tsx works."
    classification = IntentRouter.classify(query)
    assert classification.intent == AssistantIntent.CODE_EXPLANATION

    result = await reasoning_svc.generate_response(
        user_message=query,
        context=context,
        classification=classification,
    )

    # ANTI-HIJACKING ASSERTION: Action must be stripped for CODE_EXPLANATION!
    assert result.suggested_action is None, "RUN_STATIC_ANALYSIS was erroneously accepted for a code explanation query!"


# -----------------------------------------------------------------------------
# 5. Verification Troubleshooting Explicit Request
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_verification_troubleshooting_allowed():
    """Verify that when a user explicitly asks about verification, RUN_STATIC_ANALYSIS is permitted."""
    mock_provider = MockLLMProvider()
    troubleshoot_reply = AssistantResponseSchema(
        message="The version verification failed because a static analysis report is missing. I can trigger static analysis now.",
        suggested_action=AssistantActionCandidate(
            action_id="RUN_STATIC_ANALYSIS",
            parameters={},
        ),
    )
    mock_provider.register_structured_response(troubleshoot_reply)

    reasoning_svc = AssistantReasoningService(provider=mock_provider)
    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
        active_version_number=3,
        active_version_status="FAILED_VERIFICATION",
        verification_summary="Verification failed with 1 issue(s): Missing mandatory static analysis report",
    )

    query = "Why did verification fail? Please run static analysis to check linting."
    classification = IntentRouter.classify(query)
    assert classification.intent == AssistantIntent.VERIFICATION_TROUBLESHOOTING
    assert classification.allow_actions is True

    result = await reasoning_svc.generate_response(
        user_message=query,
        context=context,
        classification=classification,
    )

    assert result.suggested_action is not None
    assert result.suggested_action.action_id == "RUN_STATIC_ANALYSIS"


# -----------------------------------------------------------------------------
# 6. Ambiguous Requirements Handling
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_ambiguous_requirements_clarification():
    """Verify assistant asks clarifying questions when a feature request is underspecified."""
    mock_provider = MockLLMProvider()
    clarification_reply = AssistantResponseSchema(
        message=(
            "I'd be glad to help add notifications to MiniTask. Before we plan the implementation, could you clarify:\n"
            "1. Do you prefer in-app toast notifications for actions (e.g. task completed/deleted)?\n"
            "2. Or browser desktop notifications with permission requests?\n"
            "3. Should notifications persist across page reloads?"
        ),
        suggested_action=None,
    )
    mock_provider.register_structured_response(clarification_reply)

    reasoning_svc = AssistantReasoningService(provider=mock_provider)
    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
    )

    query = "Add notifications to the app."
    classification = IntentRouter.classify(query)

    result = await reasoning_svc.generate_response(
        user_message=query,
        context=context,
        classification=classification,
    )

    assert "?" in result.message
    assert "clarify" in result.message.lower() or "toast" in result.message.lower()
    assert result.suggested_action is None


# -----------------------------------------------------------------------------
# 7. Follow-up Context Continuity
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_followup_continuity():
    """Verify follow-up inquiries inherit prior conversational context accurately."""
    history = [
        {"role": "user", "content": "Explain how filtering works in frontend/src/App.tsx."},
        {"role": "assistant", "content": "Filtering is controlled by the `filter` state ('ALL' | 'PENDING' | 'COMPLETED')."},
    ]

    followup_query = "whats the matter then?"
    # If prior context was discussing a preview bug
    preview_history = [
        {"role": "user", "content": "the changes are not seen in live preview"},
        {"role": "assistant", "content": "The Live Preview runtime is serving in template mode on port 8001."},
    ]
    res_preview = IntentRouter.classify(followup_query, history_messages=preview_history)
    assert res_preview.intent == AssistantIntent.DEBUGGING
    assert res_preview.diagnostic_focus == "preview_runtime"

    # If prior context was code explanation
    res_code = IntentRouter.classify("explain more about tasks", history_messages=history)
    assert res_code.intent == AssistantIntent.CODE_EXPLANATION


# -----------------------------------------------------------------------------
# 8. Multi-File Feature Planning (Anti-Hijacking by Fast Path)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_multi_file_feature_planning():
    """Verify detailed task specs with acceptance criteria are routed to planning, not hijacked by fast-path."""
    spec_query = """**Task Name:** Add Task Categories and Dashboard Analytics

**Description:**
Enhance the existing MiniTask React application by adding categories (Work, Personal, Urgent) with filter tabs and real-time completion analytics.

**Acceptance Criteria:**
1. Users can select category when creating tasks.
2. Category badges appear on cards.
3. Dashboard statistics update automatically.
4. Categories persist in localStorage."""

    classification = IntentRouter.classify(spec_query)
    assert classification.intent == AssistantIntent.FEATURE_PLANNING
    assert classification.is_fast_path_candidate is False, "Complex spec must not be fast-path candidate"

    # Fast-path intent classifier on AssistantReasoningService must return None
    fast_path_res = AssistantReasoningService.classify_development_intent(spec_query)
    assert fast_path_res is None, "Structured task specification was hijacked by fast-path!"


# -----------------------------------------------------------------------------
# 9. Provider Timeout and Rate Limits
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_provider_rate_limit_and_timeout():
    """Verify system handles transient rate limits with bounded retries and raises ProviderError safely."""
    mock_provider = MockLLMProvider()
    mock_provider.simulate_transient_failures(count=1)
    mock_provider.register_structured_response(
        AssistantResponseSchema(message="Recovered after transient rate limit.", suggested_action=None)
    )

    reasoning_svc = AssistantReasoningService(provider=mock_provider)
    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
    )

    # First attempt raises TransientProviderError
    with pytest.raises(TransientProviderError):
        await reasoning_svc.generate_response(user_message="Hello", context=context)

    # Subsequent attempt succeeds
    res = await reasoning_svc.generate_response(user_message="Hello", context=context)
    assert "Recovered" in res.message


# -----------------------------------------------------------------------------
# 10. Cross-Project Data Isolation
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_cross_project_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verify conversation and context from Project A cannot be accessed under Project B."""
    owner_id = uuid.uuid4()
    proj_a = Project(id=uuid.uuid4(), name="Project A", slug="proj-a", status=ProjectStatus.IN_PROGRESS, owner_id=owner_id)
    proj_b = Project(id=uuid.uuid4(), name="Project B", slug="proj-b", status=ProjectStatus.IN_PROGRESS, owner_id=owner_id)
    db_session.add_all([proj_a, proj_b])
    await db_session.commit()

    # Create conversation under Project A
    conv_a = AssistantConversation(
        id=uuid.uuid4(),
        project_id=proj_a.id,
        user_id=owner_id,
        title="Project A Chat",
    )
    db_session.add(conv_a)
    await db_session.commit()

    # Attempt to retrieve Conversation A via Project B's API endpoint
    resp = await client.get(f"/api/v1/projects/{proj_b.id}/assistant/conversations/{conv_a.id}/messages")
    assert resp.status_code == 404, "Cross-project conversation leakage detected!"


# -----------------------------------------------------------------------------
# 11. Truthful Reporting (No Fake Tests or Fake File Writes)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_truthful_reporting_invariants():
    """Verify assistant prompt mandates that unexecuted tests or unsaved files must not be reported as passed."""
    provider = MockLLMProvider()
    svc = AssistantReasoningService(provider=provider)
    classification = IntentClassificationResult(
        intent=AssistantIntent.CODE_EXPLANATION,
        persona="IntelliDev",
        confidence=1.0,
        reasoning="Code explanation",
        allow_actions=False,
    )
    sys_prompt = svc._build_system_instruction(classification)

    assert "NEVER pretend to have read a file that is not in the context" in sys_prompt
    assert "Never claim a test or build succeeded unless verified execution data is present" in sys_prompt
    assert "Do NOT output fake percentage progress" in sys_prompt
    assert "NEVER respond with arbitrary human-developer time estimates" in sys_prompt


# -----------------------------------------------------------------------------
# 12. Code Modification Intent Routing and Proposal Lifecycle
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_code_modification_routing_and_proposal():
    """Verify code modification requests route to CODE_MODIFICATION and allow APPLY_CODE_CHANGE proposals."""
    query = "Please update frontend/src/App.tsx to add a Clear Completed button."
    classification = IntentRouter.classify(query)
    assert classification.intent == AssistantIntent.CODE_MODIFICATION
    assert classification.persona == "IntelliDev"
    assert classification.allow_actions is True

    # Informational queries must NOT route to CODE_MODIFICATION
    info_query = "Explain how to modify frontend/src/App.tsx."
    info_classification = IntentRouter.classify(info_query)
    assert info_classification.intent == AssistantIntent.CODE_EXPLANATION
    assert info_classification.allow_actions is False

    mock_provider = MockLLMProvider()
    action_candidate = AssistantActionCandidate(
        action_id="APPLY_CODE_CHANGE",
        parameters={
            "version_id": str(uuid.uuid4()),
            "reason": "Add Clear Completed button to task manager",
            "changes": [
                {
                    "file_path": "frontend/src/App.tsx",
                    "content": "export function App() { return <button>Clear Completed</button>; }",
                }
            ],
        },
    )
    reply = AssistantResponseSchema(
        message="I have prepared the code changes to add a Clear Completed button to App.tsx. Please review the diff.",
        suggested_action=action_candidate,
    )
    mock_provider.register_structured_response(reply)

    reasoning_svc = AssistantReasoningService(provider=mock_provider)
    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
        active_version_number=3,
        active_version_status="VERIFIED",
        retrieved_files=[
            {
                "path": "frontend/src/App.tsx",
                "language": "typescript",
                "size_bytes": 1024,
                "content": "export function App() { const [tasks, setTasks] = useState([]); }",
            }
        ],
    )

    result = await reasoning_svc.generate_response(
        user_message=query,
        context=context,
        classification=classification,
    )

    assert result.suggested_action is not None
    assert result.suggested_action.action_id == "APPLY_CODE_CHANGE"
    assert "Clear Completed" in result.message
    assert result.intent == AssistantIntent.CODE_MODIFICATION.value


# -----------------------------------------------------------------------------
# 13. Preview Synchronization Contract & Action Payload Integrity
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_code_change_dispatch_payload_contract():
    """Verify APPLY_CODE_CHANGE returns top-level version_id and new_version dictionary for UI synchronization."""
    from app.services.engineering_action_service import EngineeringActionService

    project_id = uuid.uuid4()
    version_id = uuid.uuid4()

    active_version_mock = MagicMock()
    active_version_mock.id = version_id
    active_version_mock.version_id = version_id
    active_version_mock.version_number = 3
    active_version_mock.requirement_ids = []
    active_version_mock.files_manifest = [{"path": "frontend/src/App.tsx", "size_bytes": 100, "language": "typescript"}]

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = active_version_mock
    mock_res.scalars.return_value.first.return_value = 3
    mock_db.execute = AsyncMock(return_value=mock_res)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()

    version_svc = MagicMock()
    version_svc.sanitize_file_path = lambda p: p.replace("\\", "/").strip().lstrip("/")
    version_svc.compute_content_hash = lambda files: "hash123"
    version_svc.compute_manifest_hash = lambda files: "mhash123"
    version_svc.get_active_version = AsyncMock(return_value=active_version_mock)
    version_svc._resolve_version_files_map = AsyncMock(return_value={"frontend/src/App.tsx": "export function App() {}"})
    version_svc._resolve_project = AsyncMock(return_value=MagicMock(settings={}))

    service = EngineeringActionService(
        session=mock_db,
        version_service=version_svc,
        verification_service=MagicMock(),
        requirement_service=MagicMock(),
        context_engine=MagicMock(),
        workflow_service=MagicMock(),
    )

    result_payload, summary = await service._dispatch_action(
        project_id=project_id,
        action_id="APPLY_CODE_CHANGE",
        parameters={
            "version_id": str(version_id),
            "reason": "Add Clear Completed button",
            "changes": [{"file_path": "frontend/src/App.tsx", "content": "export function App() {}"}],
        },
        target_id=None,
        user_id="assistant_user",
    )

    # Invariant: Must return top-level version_id, version_number, and new_version dict
    assert "version_id" in result_payload
    assert result_payload["version_number"] == 4
    assert "new_version" in result_payload
    assert result_payload["new_version"]["id"] == result_payload["version_id"]
    assert result_payload["new_version"]["version_number"] == 4
    assert result_payload["new_version"]["verification_summary"] is not None


