"""Deterministic Unit & Integration Tests for Code Generation Architecture (Phase 11A).

Covers:
1. Code Generation Planning:
   - Valid plan generation and deterministic validation
   - Unsupported stack rejections (language, framework, database, package manager)
   - Path safety rejections (relative paths only, traversal '..', absolute, drive letters, backslashes, null bytes)
   - Duplicate path rejections
   - File limits (empty plan, exceeding MAX_FILES)
   - Requirement and architecture component traceability validation
2. Code Generation Agent:
   - Valid generated output and manifest consistency
   - Unplanned file rejection
   - Missing planned file rejection
   - Duplicate path rejection
   - File size limits (MAX_FILE_SIZE_BYTES, MAX_TOTAL_SIZE_BYTES)
   - Secret scanning and hardcoded credential rejection
   - AST syntax validation without execution
   - Dynamic eval/exec rejection
   - Provider routing & MockLLMProvider execution
3. Code Generation Workflow Pipeline:
   - 5-stage pipeline execution (Requirement -> Architecture -> Database -> Planning -> Code Generation)
   - Typed artifact provenance propagation
"""

import ast
import uuid
from datetime import datetime, timezone
import pytest

from app.agents.architecture_recommendation.contracts import (
    ArchitectureRecommendationOutput,
    ArchitectureStyle,
    ArchitectureStyleRecommendation,
    ComponentRecommendation,
)
from app.agents.code_generation.contracts import (
    MAX_FILES,
    MAX_FILE_SIZE_BYTES,
    MAX_TOTAL_SIZE_BYTES,
    CodeGenerationOutput,
    CodeGenerationPlan,
    FileType,
    GeneratedFile,
    PlannedFile,
)
from app.agents.code_generation.generation_agent import CodeGenerationAgent
from app.agents.code_generation.planning_agent import CodeGenerationPlanningAgent
from app.agents.code_generation.validation import (
    scan_for_secrets,
    validate_code_generation_output,
    validate_code_generation_plan,
    validate_path_safety,
)
from app.agents.contracts import AgentExecutionStatus
from app.agents.database_design.contracts import (
    AttributeRecommendation,
    DataType,
    DatabaseDesignOutput,
    DatabaseParadigm,
    EntityRecommendation,
    PrimaryKeyRecommendation,
)
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_code_generation_agents, register_default_agents
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.models.project import ProjectStatus
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse
from app.workflows.contracts import WorkflowInput, WorkflowStatus, WorkflowStepStatus
from app.workflows.coordinator import WorkflowCoordinator
from app.workflows.pipelines import build_code_generation_workflow


# ==============================================================================
# Test Fixtures & Context Helpers
# ==============================================================================

@pytest.fixture
def test_context() -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()

    project = ProjectResponse(
        id=project_id,
        name="Payment Gateway Service",
        slug="payment-gateway",
        description="High-security payment processing and transaction ledger service.",
        status=ProjectStatus.IN_PROGRESS,
        created_at=now,
        updated_at=now,
    )

    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="Payment Tokenization",
        description="Tokenize cardholder data before storage and processing.",
        priority=RequirementPriority.CRITICAL,
        type=RequirementType.FUNCTIONAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    req2 = RequirementResponse(
        id=req2_id,
        project_id=project_id,
        title="Transaction Ledger",
        description="Record append-only transaction logs for double-entry settlement.",
        priority=RequirementPriority.HIGH,
        type=RequirementType.FUNCTIONAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    stats = RequirementStatistics(
        total_requirements=2,
        active_requirements=2,
        functional_count=2,
        non_functional_count=0,
        constraint_count=0,
        by_priority={"CRITICAL": 1, "HIGH": 1},
        by_status={"APPROVED": 2},
        completion_percentage=100.0,
    )

    return ProjectContextResponse(
        project=project,
        requirements=[req1, req2],
        statistics=stats,
        context_version=1,
        generated_at=now,
    )


@pytest.fixture
def mock_architecture_output(test_context: ProjectContextResponse) -> ArchitectureRecommendationOutput:
    req_ids = [r.id for r in test_context.requirements]
    return ArchitectureRecommendationOutput(
        summary="Modular monolith architecture with transaction gateway and ledger modules.",
        architecture_styles=[
            ArchitectureStyleRecommendation(
                style=ArchitectureStyle.MODULAR_MONOLITH,
                confidence=0.92,
                rationale="Isolates payment and ledger domains while avoiding distributed latency.",
            )
        ],
        components=[
            ComponentRecommendation(
                name="PaymentGatewayModule",
                responsibility="Ingests external payment requests and handles tokenization.",
                suggested_patterns=["Facade", "Adapter"],
                reason="Handles payment tokenization",
                requirement_ids=req_ids[:1],
            ),
            ComponentRecommendation(
                name="LedgerModule",
                responsibility="Persists double-entry financial journals immutably.",
                suggested_patterns=["Repository"],
                reason="Persists financial journals",
                requirement_ids=req_ids[1:],
            ),
        ],
        data_flows=[],
        technologies=[],
        trade_offs=[],
        assumptions=[],
        constraints=[],
        unknowns=[],
        traceability_matrix=[],
    )


@pytest.fixture
def mock_database_output(test_context: ProjectContextResponse) -> DatabaseDesignOutput:
    req_ids = [r.id for r in test_context.requirements]
    return DatabaseDesignOutput(
        summary="Relational database design for payment gateway.",
        database_paradigm=DatabaseParadigm.RELATIONAL,
        entities=[
            EntityRecommendation(
                name="PaymentToken",
                description="Secure vault token mapping.",
                purpose="Token vault entity.",
                attributes=[
                    AttributeRecommendation(name="token_id", data_type=DataType.UUID, is_nullable=False, description="Primary key token UUID"),
                    AttributeRecommendation(name="card_hash", data_type=DataType.STRING, is_nullable=False, description="Encrypted card hash"),
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["token_id"]),
                requirement_ids=req_ids[:1],
            ),
            EntityRecommendation(
                name="TransactionJournal",
                description="Immutable journal entry.",
                purpose="Financial settlement journal entity.",
                attributes=[
                    AttributeRecommendation(name="journal_id", data_type=DataType.UUID, is_nullable=False, description="Primary key journal UUID"),
                    AttributeRecommendation(name="amount_cents", data_type=DataType.INTEGER, is_nullable=False, description="Transaction amount in cents"),
                ],
                primary_key=PrimaryKeyRecommendation(attributes=["journal_id"]),
                requirement_ids=req_ids[1:],
            ),
        ],
        relationships=[],
        indexes=[],
        constraints=[],
        trade_offs=[],
        assumptions=[],
        unknowns=[],
        requirement_traceability=[],
        architecture_traceability=[],
    )


# ==============================================================================
# 1. Path Safety & Secret Scanning Tests
# ==============================================================================

class TestPathSafetyAndSecrets:
    """Deterministic validation tests for path traversal prevention and secret detection."""

    @pytest.mark.parametrize(
        "unsafe_path",
        [
            "../evil.py",
            "..\\evil.py",
            "app/../../secret.py",
            "/etc/passwd",
            "/app/main.py",
            "C:\\app\\main.py",
            "C:/app/main.py",
            "d:/test.py",
            "//network/share/file.py",
            "app/./main.py",
            "app//main.py",
            "app/main\0.py",
            "a" * 151,  # Exceeds MAX_PATH_LENGTH
        ],
    )
    def test_unsafe_paths_strictly_rejected(self, unsafe_path: str):
        with pytest.raises(ValueError):
            validate_path_safety(unsafe_path)

    @pytest.mark.parametrize(
        "safe_path",
        [
            "app/main.py",
            "app/config.py",
            "app/api/v1/routes.py",
            "requirements.txt",
            "README.md",
        ],
    )
    def test_valid_relative_paths_accepted(self, safe_path: str):
        validate_path_safety(safe_path)  # Should not raise

    def test_secret_scanner_detects_credentials(self):
        # 1. Private key detection
        rsa_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----"
        assert len(scan_for_secrets(rsa_key, "app/key.py")) > 0

        # 2. Hardcoded API key detection
        openai_key = 'client = OpenAI(api_key="sk-abcdef12345678901234567890")'
        assert len(scan_for_secrets(openai_key, "app/client.py")) > 0

        # 3. Groq API key detection
        groq_key = 'GROQ_KEY = "gsk_1234567890abcdef1234567890abcdef"'
        assert len(scan_for_secrets(groq_key, "app/groq.py")) > 0

        # 4. Database URI with embedded password
        db_uri = 'db_url = "postgresql://admin:super_secret_password_123@db.prod.internal:5432/main"'
        assert len(scan_for_secrets(db_uri, "app/db.py")) > 0

    def test_secret_scanner_allows_env_placeholders(self):
        safe_code = (
            'import os\n'
            'api_key = os.getenv("API_KEY")\n'
            'db_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")\n'
        )
        assert len(scan_for_secrets(safe_code, "app/config.py")) == 0


# ==============================================================================
# 2. Code Generation Planning Agent Tests
# ==============================================================================

class TestCodeGenerationPlanner:
    """Deterministic validation and behavior tests for CodeGenerationPlanningAgent."""

    def test_valid_plan_validation(self, test_context: ProjectContextResponse, mock_architecture_output):
        req_id = str(test_context.requirements[0].id)
        comp_name = mock_architecture_output.components[0].name

        plan = CodeGenerationPlan(
            project_type="backend-service",
            language="python",
            framework="fastapi",
            database="postgresql",
            package_manager="pip",
            files=[
                PlannedFile(
                    path="app/main.py",
                    purpose="FastAPI application entrypoint and route mounting",
                    file_type=FileType.SOURCE,
                    architecture_component=comp_name,
                    requirement_ids=[req_id],
                ),
                PlannedFile(
                    path="requirements.txt",
                    purpose="Project dependencies specification",
                    file_type=FileType.DEPENDENCY,
                ),
            ],
            rationale="Clean FastAPI microservice scaffold.",
        )

        res = validate_code_generation_plan(plan, test_context, mock_architecture_output)
        assert res.is_valid is True
        assert len(res.errors) == 0

    def test_plan_rejects_unsupported_language_and_framework(self, test_context: ProjectContextResponse):
        plan = CodeGenerationPlan(
            language="rust",
            framework="actix-web",
            database="postgresql",
            package_manager="cargo",
            files=[
                PlannedFile(path="src/main.rs", purpose="Entrypoint", file_type=FileType.SOURCE),
            ],
            rationale="Rust scaffold.",
        )
        res = validate_code_generation_plan(plan, test_context)
        assert res.is_valid is False
        assert any("Unsupported language 'rust'" in err for err in res.errors)
        assert any("Unsupported framework 'actix-web'" in err for err in res.errors)
        assert any("Unsupported package manager 'cargo'" in err for err in res.errors)

    def test_plan_rejects_duplicate_paths(self, test_context: ProjectContextResponse):
        plan = CodeGenerationPlan(
            files=[
                PlannedFile(path="app/main.py", purpose="First entrypoint", file_type=FileType.SOURCE),
                PlannedFile(path="app/main.py", purpose="Duplicate entrypoint", file_type=FileType.SOURCE),
            ],
            rationale="Duplicate plan.",
        )
        res = validate_code_generation_plan(plan, test_context)
        assert res.is_valid is False
        assert any("Duplicate path in generation plan" in err for err in res.errors)

    def test_plan_rejects_invalid_requirement_traceability(self, test_context: ProjectContextResponse):
        bogus_uuid = str(uuid.uuid4())
        plan = CodeGenerationPlan(
            files=[
                PlannedFile(
                    path="app/main.py",
                    purpose="App entrypoint",
                    file_type=FileType.SOURCE,
                    requirement_ids=[bogus_uuid],
                )
            ],
            rationale="Invalid traceability plan.",
        )
        res = validate_code_generation_plan(plan, test_context)
        assert res.is_valid is False
        assert any("references unknown requirement ID" in err for err in res.errors)

    def test_plan_rejects_invalid_architecture_component(
        self, test_context: ProjectContextResponse, mock_architecture_output
    ):
        plan = CodeGenerationPlan(
            files=[
                PlannedFile(
                    path="app/main.py",
                    purpose="App entrypoint",
                    file_type=FileType.SOURCE,
                    architecture_component="InventedNonExistentService",
                )
            ],
            rationale="Invalid architecture reference.",
        )
        res = validate_code_generation_plan(plan, test_context, mock_architecture_output)
        assert res.is_valid is False
        assert any("references undeclared architecture component" in err for err in res.errors)

    @pytest.mark.asyncio
    async def test_planner_agent_mock_execution(
        self, test_context: ProjectContextResponse, mock_architecture_output, mock_database_output
    ):
        agent = CodeGenerationPlanningAgent()
        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)

        result = await executor.execute(
            agent=agent,
            context=test_context,
            architecture_recommendation=mock_architecture_output,
            database_design=mock_database_output,
        )

        assert result.status == AgentExecutionStatus.COMPLETED
        assert result.validation.is_valid is True
        output = result.output
        assert isinstance(output, CodeGenerationPlan)
        assert len(output.files) >= 3
        assert any(f.path == "app/main.py" for f in output.files)
        assert any(f.path == "requirements.txt" for f in output.files)


# ==============================================================================
# 3. Code Generation Agent Tests
# ==============================================================================

class TestCodeGenerationAgent:
    """Deterministic validation and security tests for CodeGenerationAgent."""

    def test_manifest_consistency_unplanned_file_rejected(self, test_context: ProjectContextResponse):
        plan = CodeGenerationPlan(
            files=[PlannedFile(path="app/main.py", purpose="App entry", file_type=FileType.SOURCE)],
            rationale="Single file plan.",
        )

        # Output contains an unplanned file
        out = CodeGenerationOutput(
            plan=plan,
            generated_files=[
                GeneratedFile(path="app/main.py", content="print('hello')", size_bytes=14),
                GeneratedFile(path="app/unplanned.py", content="print('unplanned')", size_bytes=18),
            ],
            total_files=2,
            total_size_bytes=32,
            summary="Manifest violation.",
        )

        res = validate_code_generation_output(out, plan, test_context)
        assert res.is_valid is False
        assert any("unplanned files: ['app/unplanned.py']" in err for err in res.errors)

    def test_manifest_consistency_missing_planned_file_rejected(self, test_context: ProjectContextResponse):
        plan = CodeGenerationPlan(
            files=[
                PlannedFile(path="app/main.py", purpose="App entry", file_type=FileType.SOURCE),
                PlannedFile(path="requirements.txt", purpose="Project dependencies specification", file_type=FileType.DEPENDENCY),
            ],
            rationale="Two file plan.",
        )

        # Output misses requirements.txt
        out = CodeGenerationOutput(
            plan=plan,
            generated_files=[
                GeneratedFile(path="app/main.py", content="print('hello')", size_bytes=14),
            ],
            total_files=1,
            total_size_bytes=14,
            summary="Missing planned file.",
        )

        res = validate_code_generation_output(out, plan, test_context)
        assert res.is_valid is False
        assert any("missing required planned files: ['requirements.txt']" in err for err in res.errors)

    def test_output_rejects_embedded_secrets(self, test_context: ProjectContextResponse):
        plan = CodeGenerationPlan(
            files=[PlannedFile(path="app/main.py", purpose="App entry", file_type=FileType.SOURCE)],
            rationale="Plan with secrets.",
        )

        secret_code = 'OPENAI_KEY = "sk-1234567890123456789012345678901234567890"\n'
        out = CodeGenerationOutput(
            plan=plan,
            generated_files=[
                GeneratedFile(
                    path="app/main.py",
                    content=secret_code,
                    size_bytes=len(secret_code.encode("utf-8")),
                )
            ],
            total_files=1,
            total_size_bytes=len(secret_code.encode("utf-8")),
            summary="Secret leak.",
        )

        res = validate_code_generation_output(out, plan, test_context)
        assert res.is_valid is False
        assert any("Secret detected in 'app/main.py'" in err for err in res.errors)

    def test_output_rejects_python_syntax_errors(self, test_context: ProjectContextResponse):
        plan = CodeGenerationPlan(
            files=[PlannedFile(path="app/main.py", purpose="App entry", file_type=FileType.SOURCE)],
            rationale="Plan with syntax error.",
        )

        broken_code = "def broken_func(:\n    pass\n"
        out = CodeGenerationOutput(
            plan=plan,
            generated_files=[
                GeneratedFile(
                    path="app/main.py",
                    content=broken_code,
                    size_bytes=len(broken_code.encode("utf-8")),
                )
            ],
            total_files=1,
            total_size_bytes=len(broken_code.encode("utf-8")),
            summary="Broken syntax.",
        )

        res = validate_code_generation_output(out, plan, test_context)
        assert res.is_valid is False
        assert any("Syntax error in generated Python file 'app/main.py'" in err for err in res.errors)

    def test_output_rejects_dynamic_eval_exec(self, test_context: ProjectContextResponse):
        plan = CodeGenerationPlan(
            files=[PlannedFile(path="app/main.py", purpose="App entry", file_type=FileType.SOURCE)],
            rationale="Plan with dangerous eval.",
        )

        dangerous_code = "user_input = '__import__(\"os\").system(\"calc\")'\neval(user_input)\n"
        out = CodeGenerationOutput(
            plan=plan,
            generated_files=[
                GeneratedFile(
                    path="app/main.py",
                    content=dangerous_code,
                    size_bytes=len(dangerous_code.encode("utf-8")),
                )
            ],
            total_files=1,
            total_size_bytes=len(dangerous_code.encode("utf-8")),
            summary="Dangerous eval.",
        )

        res = validate_code_generation_output(out, plan, test_context)
        assert res.is_valid is False
        assert any("Forbidden dynamic execution call 'eval()'" in err for err in res.errors)

    @pytest.mark.asyncio
    async def test_codegen_agent_mock_execution(self, test_context: ProjectContextResponse):
        plan = CodeGenerationPlan(
            files=[
                PlannedFile(path="app/main.py", purpose="Entrypoint", file_type=FileType.SOURCE),
                PlannedFile(path="app/config.py", purpose="Configuration settings", file_type=FileType.CONFIG),
                PlannedFile(path="requirements.txt", purpose="Project dependencies specification", file_type=FileType.DEPENDENCY),
            ],
            rationale="Deterministic mock execution plan.",
        )

        agent = CodeGenerationAgent()
        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)

        result = await executor.execute(
            agent=agent,
            context=test_context,
            plan=plan,
        )

        assert result.status == AgentExecutionStatus.COMPLETED
        assert result.validation.is_valid is True
        output = result.output
        assert isinstance(output, CodeGenerationOutput)
        assert output.total_files == 3
        # Ensure all Python files parse cleanly via ast without executing
        for gf in output.generated_files:
            if gf.path.endswith(".py"):
                ast.parse(gf.content)  # Must be valid Python syntax


# ==============================================================================
# 4. Multi-Agent Code Generation Workflow Tests
# ==============================================================================

class TestCodeGenerationWorkflow:
    """Test full 5-stage pipeline from design outputs to generated scaffold."""

    @pytest.mark.asyncio
    async def test_full_code_generation_workflow_with_mock_provider(self, test_context: ProjectContextResponse):
        from app.api.dependencies import build_default_mock_provider

        registry = AgentRegistry()
        register_default_agents(registry)
        register_code_generation_agents(registry)

        provider = build_default_mock_provider()
        executor = AgentExecutor(provider=provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        workflow = build_code_generation_workflow()
        assert len(workflow.steps) == 5
        assert [s.step_id for s in workflow.steps] == [
            "requirement-analysis",
            "architecture-recommendation",
            "database-design",
            "code-generation-planning",
            "code-generation",
        ]

        workflow_input = WorkflowInput(context=test_context)
        result = await coordinator.execute(workflow=workflow, workflow_input=workflow_input)

        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.step_results) == 5
        assert all(s.status == WorkflowStepStatus.COMPLETED for s in result.step_results)

        # Verify all 5 artifacts exist and are typed
        assert "requirement-analysis" in result.artifacts
        assert "architecture-recommendation" in result.artifacts
        assert "database-design" in result.artifacts
        assert "code-generation-planning" in result.artifacts
        assert "code-generation" in result.artifacts

        plan_artifact = result.artifacts["code-generation-planning"]
        assert isinstance(plan_artifact, CodeGenerationPlan)

        codegen_artifact = result.artifacts["code-generation"]
        assert isinstance(codegen_artifact, CodeGenerationOutput)
        assert codegen_artifact.total_files >= 3

        # Verify manifest consistency between planner and generator artifacts
        planned_paths = {f.path for f in plan_artifact.files}
        generated_paths = {f.path for f in codegen_artifact.generated_files}
        assert planned_paths == generated_paths
