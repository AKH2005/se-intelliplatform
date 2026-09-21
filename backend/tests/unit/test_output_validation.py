"""Unit Tests for Two-Stage Validation Pipeline."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import BaseModel, Field

from app.agents.contracts import ValidationResult
from app.agents.exceptions import AgentValidationError
from app.agents.validation import DeterministicValidator
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


class SampleStructuredOutput(BaseModel):
    plan_name: str = Field(..., min_length=2)
    estimated_hours: int = Field(..., ge=1, le=1000)


@pytest.fixture
def empty_context() -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="P",
            slug="p",
            status="DRAFT",
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


def test_stage1_valid_schema_from_dict():
    """Verify structural schema validation passes for valid dictionary."""
    data = {"plan_name": "Sprint 1", "estimated_hours": 40}
    model, res = DeterministicValidator.validate_schema(data, SampleStructuredOutput)
    assert res.is_valid is True
    assert model is not None
    assert model.plan_name == "Sprint 1"
    assert model.estimated_hours == 40


def test_stage1_invalid_schema_fails():
    """Verify structural schema validation fails for type and constraint violations."""
    # Negative hours violates ge=1
    bad_data = {"plan_name": "Sprint 1", "estimated_hours": -5}
    model, res = DeterministicValidator.validate_schema(bad_data, SampleStructuredOutput)
    assert res.is_valid is False
    assert model is None
    assert len(res.errors) >= 1
    assert "estimated_hours" in res.errors[0]


def test_stage2_deterministic_business_hook_rejection(empty_context: ProjectContextResponse):
    """Verify deterministic domain validation rejects structurally valid data that violates business rules."""
    valid_struct = {"plan_name": "Large Migration", "estimated_hours": 900}

    def business_rule_hook(output: SampleStructuredOutput, ctx: ProjectContextResponse) -> ValidationResult:
        # Enforce business rule: plans over 500 hours must be rejected as un-scoped
        if output.estimated_hours > 500:
            return ValidationResult(
                is_valid=False,
                errors=["Business rule: single sprint plan cannot exceed 500 hours."],
            )
        return ValidationResult(is_valid=True)

    with pytest.raises(AgentValidationError) as exc_info:
        DeterministicValidator.run_pipeline(
            raw_output=valid_struct,
            schema=SampleStructuredOutput,
            context=empty_context,
            domain_validator=business_rule_hook,
        )
    assert "cannot exceed 500 hours" in str(exc_info.value)


def test_stage2_deterministic_business_hook_success(empty_context: ProjectContextResponse):
    """Verify pipeline accepts output when both schema and business validation pass."""
    valid_struct = {"plan_name": "Micro Sprint", "estimated_hours": 24}

    def business_rule_hook(output: SampleStructuredOutput, ctx: ProjectContextResponse) -> ValidationResult:
        return ValidationResult(is_valid=True)

    model, res = DeterministicValidator.run_pipeline(
        raw_output=valid_struct,
        schema=SampleStructuredOutput,
        context=empty_context,
        domain_validator=business_rule_hook,
    )
    assert res.is_valid is True
    assert model.plan_name == "Micro Sprint"
