"""Unit tests for Phase 8.0 Test Case Generation Agent contracts and deterministic validation."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.contracts import ValidationResult
from app.agents.test_case_generation.contracts import (
    DEFAULT_TEST_CASE_LIMITATIONS,
    TestCase,
    TestCaseCoverage,
    TestCaseGenerationCandidate,
    TestCaseGenerationOutput,
    TestPriority,
    TestStep,
    TestType,
)
from app.agents.test_case_generation.validation import (
    get_active_requirement_ids,
    get_all_context_requirement_ids,
    validate_test_case_generation_output,
)
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.fixture
def mock_context_with_reqs():
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()
    req_deferred_id = uuid.uuid4()
    req_rejected_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="User Authentication",
        description="Users must authenticate using JWT tokens.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req2 = RequirementResponse(
        id=req2_id,
        project_id=project_id,
        title="Password Reset",
        description="Users can request a password reset email.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.MEDIUM,
        status=RequirementStatus.DRAFT,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req_deferred = RequirementResponse(
        id=req_deferred_id,
        project_id=project_id,
        title="Biometric Login",
        description="Users can log in with fingerprint.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.LOW,
        status=RequirementStatus.DEFERRED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req_rejected = RequirementResponse(
        id=req_rejected_id,
        project_id=project_id,
        title="Legacy Insecure Auth",
        description="Basic auth over HTTP.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.LOW,
        status=RequirementStatus.REJECTED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    context = ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="Auth Service",
            slug="auth-service",
            description="Testing contracts",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        requirements=[req1, req2, req_deferred, req_rejected],
        statistics=RequirementStatistics(
            total_requirements=4,
            active_requirements=2,
            functional_count=4,
            non_functional_count=0,
            constraint_count=0,
            by_priority={"HIGH": 1, "MEDIUM": 1, "LOW": 2},
            by_status={"APPROVED": 1, "DRAFT": 1, "DEFERRED": 1, "REJECTED": 1},
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )
    return context, req1_id, req2_id, req_deferred_id, req_rejected_id


def test_active_requirements_extraction(mock_context_with_reqs):
    context, req1_id, req2_id, req_deferred_id, req_rejected_id = mock_context_with_reqs
    active_ids = get_active_requirement_ids(context)
    assert str(req1_id) in active_ids
    assert str(req2_id) in active_ids
    assert str(req_deferred_id) not in active_ids
    assert str(req_rejected_id) not in active_ids
    assert len(active_ids) == 2

    all_ids = get_all_context_requirement_ids(context)
    assert len(all_ids) == 4
    assert all_ids[str(req_deferred_id)] == RequirementStatus.DEFERRED.value


def test_valid_test_case_generation_output(mock_context_with_reqs):
    context, req1_id, req2_id, _, _ = mock_context_with_reqs
    tc1 = TestCase(
        test_case_id="TC-001",
        title="Successful JWT Login",
        description="Verify valid credentials yield JWT token.",
        test_type=TestType.INTEGRATION,
        priority=TestPriority.HIGH,
        preconditions=["User account exists and is active."],
        steps=[
            TestStep(step_number=1, action="Send POST /api/v1/auth/login with valid creds", expected_behavior="Status 200 returned"),
            TestStep(step_number=2, action="Inspect response body", expected_behavior="Valid JWT token present"),
        ],
        expected_result="User successfully authenticated with JWT.",
        requirement_ids=[str(req1_id)],
    )
    tc2 = TestCase(
        test_case_id="TC-002",
        title="Password Reset Request",
        description="Verify password reset email is dispatched.",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.MEDIUM,
        preconditions=["Email service is operational."],
        steps=[
            TestStep(step_number=1, action="Submit password reset request", expected_behavior="Status 202 accepted"),
        ],
        expected_result="Reset token dispatched to user email.",
        requirement_ids=[str(req2_id)],
    )

    output = TestCaseGenerationOutput(
        test_cases=[tc1, tc2],
        total_test_cases=2,
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=2,
            requirements_without_tests=0,
            coverage_percentage=100.0,
        ),
        summary="Comprehensive test suite covering authentication and password reset.",
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )

    result = validate_test_case_generation_output(output, context)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validation_fails_on_count_mismatch(mock_context_with_reqs):
    context, req1_id, _, _, _ = mock_context_with_reqs
    tc1 = TestCase(
        test_case_id="TC-001",
        title="Valid Test",
        description="Desc",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.HIGH,
        steps=[TestStep(step_number=1, action="Action", expected_behavior="Expect")],
        expected_result="Result",
        requirement_ids=[str(req1_id)],
    )
    output = TestCaseGenerationOutput(
        summary="Count mismatch test",
        test_cases=[tc1],
        total_test_cases=99,  # Mismatch!
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=1,
            requirements_without_tests=1,
            coverage_percentage=50.0,
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    result = validate_test_case_generation_output(output, context)
    assert result.is_valid is False
    assert any("total_test_cases (99) does not match" in e for e in result.errors)


def test_validation_fails_on_duplicate_test_case_id(mock_context_with_reqs):
    context, req1_id, req2_id, _, _ = mock_context_with_reqs
    tc1 = TestCase(
        test_case_id="TC-001",
        title="Test One",
        description="Desc 1",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.HIGH,
        steps=[TestStep(step_number=1, action="Act 1", expected_behavior="Exp 1")],
        expected_result="Res 1",
        requirement_ids=[str(req1_id)],
    )
    tc2 = TestCase(
        test_case_id="TC-001",  # Duplicate ID!
        title="Test Two",
        description="Desc 2",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.LOW,
        steps=[TestStep(step_number=1, action="Act 2", expected_behavior="Exp 2")],
        expected_result="Res 2",
        requirement_ids=[str(req2_id)],
    )
    output = TestCaseGenerationOutput(
        summary="Duplicate test case id test",
        test_cases=[tc1, tc2],
        total_test_cases=2,
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=2,
            requirements_without_tests=0,
            coverage_percentage=100.0,
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    result = validate_test_case_generation_output(output, context)
    assert result.is_valid is False
    assert any("Duplicate test_case_id 'TC-001'" in e for e in result.errors)


def test_validation_fails_on_non_sequential_steps(mock_context_with_reqs):
    context, req1_id, _, _, _ = mock_context_with_reqs
    tc1 = TestCase(
        test_case_id="TC-001",
        title="Broken Steps",
        description="Desc",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.MEDIUM,
        steps=[
            TestStep(step_number=1, action="Step 1", expected_behavior="Exp 1"),
            TestStep(step_number=3, action="Step 3", expected_behavior="Exp 3"),  # Non-sequential!
        ],
        expected_result="Res",
        requirement_ids=[str(req1_id)],
    )
    output = TestCaseGenerationOutput(
        summary="Non-sequential steps test",
        test_cases=[tc1],
        total_test_cases=1,
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=1,
            requirements_without_tests=1,
            coverage_percentage=50.0,
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    result = validate_test_case_generation_output(output, context)
    assert result.is_valid is False
    assert any("step numbering must be sequential starting from 1" in e for e in result.errors)


def test_validation_fails_on_empty_action_or_behavior(mock_context_with_reqs):
    context, req1_id, _, _, _ = mock_context_with_reqs
    tc1 = TestCase(
        test_case_id="TC-001",
        title="Empty Step fields",
        description="Desc",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.MEDIUM,
        steps=[
            TestStep(step_number=1, action="   ", expected_behavior="   "),
        ],
        expected_result="Res",
        requirement_ids=[str(req1_id)],
    )
    output = TestCaseGenerationOutput(
        summary="Empty step fields test",
        test_cases=[tc1],
        total_test_cases=1,
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=1,
            requirements_without_tests=1,
            coverage_percentage=50.0,
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    result = validate_test_case_generation_output(output, context)
    assert result.is_valid is False
    assert any("action cannot be empty" in e for e in result.errors)
    assert any("expected_behavior cannot be empty" in e for e in result.errors)


def test_validation_fails_on_nonexistent_or_inactive_requirement(mock_context_with_reqs):
    context, req1_id, _, req_deferred_id, req_rejected_id = mock_context_with_reqs
    fake_req_id = str(uuid.uuid4())

    # Case A: Non-existent requirement
    tc_fake = TestCase(
        test_case_id="TC-001",
        title="Fake Req Reference",
        description="Desc",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.LOW,
        steps=[TestStep(step_number=1, action="Act", expected_behavior="Exp")],
        expected_result="Res",
        requirement_ids=[fake_req_id],
    )
    output_fake = TestCaseGenerationOutput(
        summary="Fake req test",
        test_cases=[tc_fake],
        total_test_cases=1,
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=0,
            requirements_without_tests=2,
            coverage_percentage=0.0,
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    res_fake = validate_test_case_generation_output(output_fake, context)
    assert res_fake.is_valid is False
    assert any(f"references non-existent requirement ID '{fake_req_id}'" in e for e in res_fake.errors)

    # Case B: DEFERRED requirement
    tc_deferred = TestCase(
        test_case_id="TC-002",
        title="Deferred Req Reference",
        description="Desc",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.LOW,
        steps=[TestStep(step_number=1, action="Act", expected_behavior="Exp")],
        expected_result="Res",
        requirement_ids=[str(req_deferred_id)],
    )
    output_def = TestCaseGenerationOutput(
        summary="Deferred req test",
        test_cases=[tc_deferred],
        total_test_cases=1,
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=0,
            requirements_without_tests=2,
            coverage_percentage=0.0,
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    res_def = validate_test_case_generation_output(output_def, context)
    assert res_def.is_valid is False
    assert any("with inactive status 'DEFERRED'" in e for e in res_def.errors)


def test_validation_fails_on_semantic_duplicate(mock_context_with_reqs):
    context, req1_id, _, _, _ = mock_context_with_reqs
    tc1 = TestCase(
        test_case_id="TC-001",
        title="Duplicate Case",
        description="First attempt",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.HIGH,
        steps=[TestStep(step_number=1, action="Click Login", expected_behavior="Form displayed")],
        expected_result="Form shows",
        requirement_ids=[str(req1_id)],
    )
    tc2 = TestCase(
        test_case_id="TC-002",
        title="Duplicate Case",  # Exact same title, actions, reqs
        description="Second attempt",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.HIGH,
        steps=[TestStep(step_number=1, action="Click Login", expected_behavior="Form displayed")],
        expected_result="Form shows",
        requirement_ids=[str(req1_id)],
    )
    output = TestCaseGenerationOutput(
        summary="Semantic duplicate test",
        test_cases=[tc1, tc2],
        total_test_cases=2,
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=1,
            requirements_without_tests=1,
            coverage_percentage=50.0,
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    result = validate_test_case_generation_output(output, context)
    assert result.is_valid is False
    assert any("semantic duplicate test case detected" in e for e in result.errors)


def test_validation_fails_on_coverage_tampering(mock_context_with_reqs):
    context, req1_id, _, _, _ = mock_context_with_reqs
    tc1 = TestCase(
        test_case_id="TC-001",
        title="Single Covered Test",
        description="Desc",
        test_type=TestType.FUNCTIONAL,
        priority=TestPriority.HIGH,
        steps=[TestStep(step_number=1, action="Act", expected_behavior="Exp")],
        expected_result="Res",
        requirement_ids=[str(req1_id)],
    )
    # Tampered: Claims 100% coverage and 2 requirements with tests when only 1 is tested
    output = TestCaseGenerationOutput(
        summary="Coverage tampering test",
        test_cases=[tc1],
        total_test_cases=1,
        coverage=TestCaseCoverage(
            total_active_requirements=2,
            requirements_with_tests=2,  # Tampered!
            requirements_without_tests=0,  # Tampered!
            coverage_percentage=100.0,  # Tampered!
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    result = validate_test_case_generation_output(output, context)
    assert result.is_valid is False
    assert any("requirements_with_tests mismatch" in e for e in result.errors)
    assert any("coverage_percentage mismatch" in e for e in result.errors)


def test_empty_active_requirements_zero_coverage():
    now = datetime.now(timezone.utc)
    project_id = uuid.uuid4()
    context = ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="Empty Project",
            slug="empty-proj",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        requirements=[],
        statistics=RequirementStatistics(
            total_requirements=0,
            active_requirements=0,
            functional_count=0,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )
    output = TestCaseGenerationOutput(
        summary="Empty active reqs test suite",
        test_cases=[],
        total_test_cases=0,
        coverage=TestCaseCoverage(
            total_active_requirements=0,
            requirements_with_tests=0,
            requirements_without_tests=0,
            coverage_percentage=0.0,
        ),
        limitations=DEFAULT_TEST_CASE_LIMITATIONS,
    )
    result = validate_test_case_generation_output(output, context)
    assert result.is_valid is True
    assert len(result.errors) == 0

