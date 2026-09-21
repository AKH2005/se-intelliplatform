"""Two-Stage Validation Engine: Schema & Deterministic Domain Validation."""

from collections.abc import Callable
from typing import Any, TypeVar
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.agents.contracts import ValidationResult
from app.agents.exceptions import AgentValidationError
from app.schemas.context import ProjectContextResponse

OutputT = TypeVar("OutputT", bound=BaseModel)


class DeterministicValidator:
    """Orchestrates structural schema parsing and deterministic domain business rules."""

    @classmethod
    def validate_schema(
        cls,
        raw_output: Any,
        schema: type[OutputT],
    ) -> tuple[OutputT | None, ValidationResult]:
        """Stage 1: Pydantic Structural Validation."""
        if isinstance(raw_output, schema):
            return raw_output, ValidationResult(is_valid=True)

        try:
            if isinstance(raw_output, dict):
                model_inst = schema.model_validate(raw_output)
            elif isinstance(raw_output, BaseModel):
                model_inst = schema.model_validate(raw_output.model_dump())
            elif isinstance(raw_output, str):
                model_inst = schema.model_validate_json(raw_output)
            else:
                return None, ValidationResult(
                    is_valid=False,
                    errors=[f"Unsupported output type '{type(raw_output).__name__}' for schema '{schema.__name__}'."],
                )
            return model_inst, ValidationResult(is_valid=True)
        except PydanticValidationError as pve:
            error_messages = [
                f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in pve.errors()
            ]
            return None, ValidationResult(
                is_valid=False,
                errors=error_messages,
            )
        except Exception as exc:
            return None, ValidationResult(
                is_valid=False,
                errors=[f"Failed to parse output into {schema.__name__}: {exc}"],
            )

    @classmethod
    def run_pipeline(
        cls,
        raw_output: Any,
        schema: type[OutputT],
        context: ProjectContextResponse,
        domain_validator: Callable[[OutputT, ProjectContextResponse], ValidationResult] | None = None,
    ) -> tuple[OutputT, ValidationResult]:
        """Execute Stage 1 (Schema) followed by Stage 2 (Deterministic Domain Hook).
        
        Raises AgentValidationError if either stage fails.
        """
        # Stage 1: Structural Schema Validation
        parsed_model, schema_res = cls.validate_schema(raw_output, schema)
        if not schema_res.is_valid or parsed_model is None:
            raise AgentValidationError(
                message=f"Agent output failed structural schema validation for '{schema.__name__}'.",
                validation_errors=schema_res.errors,
            )

        # Stage 2: Deterministic Domain Validation Hook
        if domain_validator is not None:
            domain_res = domain_validator(parsed_model, context)
            if not domain_res.is_valid:
                raise AgentValidationError(
                    message=f"Agent output failed deterministic business validation for '{schema.__name__}'.",
                    validation_errors=domain_res.errors,
                )
            return parsed_model, domain_res

        return parsed_model, ValidationResult(is_valid=True)
