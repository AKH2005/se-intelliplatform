"""Contracts, Data Models, and Conservative Limits for Code Generation Architecture."""

import enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# 1. Conservative Platform Limits
# ==============================================================================

MAX_FILES: int = 10
MAX_PATH_LENGTH: int = 150
MAX_FILE_SIZE_BYTES: int = 50 * 1024  # 50 KB per file
MAX_TOTAL_SIZE_BYTES: int = 200 * 1024  # 200 KB total project size

SUPPORTED_LANGUAGES: set[str] = {"python"}
SUPPORTED_FRAMEWORKS: set[str] = {"fastapi"}
SUPPORTED_DATABASES: set[str] = {"postgresql", "sqlite"}
SUPPORTED_PACKAGE_MANAGERS: set[str] = {"pip"}


# ==============================================================================
# 2. Enumerations
# ==============================================================================

class FileType(str, enum.Enum):
    """Categorical classification of generated project files."""

    SOURCE = "SOURCE"
    CONFIG = "CONFIG"
    SCHEMA = "SCHEMA"
    DOCUMENTATION = "DOCUMENTATION"
    DEPENDENCY = "DEPENDENCY"


# ==============================================================================
# 3. Code Generation Plan Models
# ==============================================================================

class PlannedFile(BaseModel):
    """Planned file entry in the deterministic generation manifest."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        ...,
        min_length=1,
        max_length=MAX_PATH_LENGTH,
        description="Relative project path (e.g. 'app/main.py')",
    )
    purpose: str = Field(
        ...,
        min_length=5,
        max_length=300,
        description="Clear engineering explanation of the file's responsibility",
    )
    file_type: FileType = Field(
        ...,
        description="Functional category of the file",
    )
    architecture_component: str | None = Field(
        default=None,
        description="Optional upstream architecture component name this file implements",
    )
    requirement_ids: list[str] = Field(
        default_factory=list,
        description="Canonical requirement UUIDs addressed by this file",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Relative paths of other planned files this file imports/depends on",
    )


class CodeGenerationPlan(BaseModel):
    """Authoritative code generation plan and file manifest."""

    model_config = ConfigDict(extra="forbid")

    project_type: str = Field(
        default="backend-service",
        description="Type of service being scaffolded",
    )
    language: str = Field(
        default="python",
        description="Programming language identifier",
    )
    framework: str = Field(
        default="fastapi",
        description="Web/application framework",
    )
    database: str = Field(
        default="postgresql",
        description="Primary database paradigm or engine",
    )
    package_manager: str = Field(
        default="pip",
        description="Dependency management tool",
    )
    files: list[PlannedFile] = Field(
        ...,
        min_length=1,
        max_length=MAX_FILES,
        description="Planned file manifest",
    )
    rationale: str = Field(
        ...,
        min_length=10,
        description="High-level engineering rationale for the chosen project structure",
    )


class PlannedFileCandidate(BaseModel):
    """Raw planned file candidate returned by LLM before validation."""

    model_config = ConfigDict(extra="ignore")

    path: str
    purpose: str
    file_type: str = "SOURCE"
    architecture_component: str | None = None
    requirement_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class CodeGenerationPlanCandidate(BaseModel):
    """Raw structured candidate returned by the LLM before validation."""

    model_config = ConfigDict(extra="ignore")

    project_type: str = Field(default="backend-service")
    language: str = Field(default="python")
    framework: str = Field(default="fastapi")
    database: str = Field(default="postgresql")
    package_manager: str = Field(default="pip")
    files: list[PlannedFileCandidate] = Field(default_factory=list)
    rationale: str = Field(default="Code generation plan proposed.")

    @field_validator("files", mode="before")
    @classmethod
    def filter_valid_planned_files(cls, v: Any) -> list[Any]:
        if not isinstance(v, list):
            return []
        return [item for item in v if isinstance(item, PlannedFileCandidate) or (isinstance(item, dict) and "path" in item and "purpose" in item)]


# ==============================================================================
# 4. Code Generation Output Models
# ==============================================================================

class GeneratedFile(BaseModel):
    """Single generated file artifact with provenance and size validation."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        ...,
        min_length=1,
        max_length=MAX_PATH_LENGTH,
        description="Relative project path matching a planned file entry",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Complete text source code content of the file",
    )
    language: str = Field(
        default="python",
        description="Language identifier for the file",
    )
    size_bytes: int = Field(
        ...,
        ge=1,
        le=MAX_FILE_SIZE_BYTES,
        description="Byte size of content encoded in UTF-8",
    )
    architecture_component: str | None = Field(
        default=None,
        description="Upstream architecture component this file implements",
    )
    requirement_ids: list[str] = Field(
        default_factory=list,
        description="Requirement UUIDs implemented in this file",
    )


class GeneratedFileCandidate(BaseModel):
    """Candidate file entry returned by LLM before size calculation and validation."""

    model_config = ConfigDict(extra="ignore")

    path: str
    content: str
    language: str = "python"
    architecture_component: str | None = None
    requirement_ids: list[str] = Field(default_factory=list)


class CodeGenerationCandidate(BaseModel):
    """Raw structured candidate output returned by LLM before deterministic validation."""

    model_config = ConfigDict(extra="ignore")

    generated_files: list[GeneratedFileCandidate] = Field(default_factory=list)
    summary: str = Field(default="Generated project scaffold files.")

    @field_validator("generated_files", mode="before")
    @classmethod
    def filter_valid_generated_files(cls, v: Any) -> list[Any]:
        if not isinstance(v, list):
            return []
        return [item for item in v if isinstance(item, GeneratedFileCandidate) or (isinstance(item, dict) and "path" in item and "content" in item)]


class CodeGenerationOutput(BaseModel):
    """Authoritative structured output of the Code Generation Agent."""

    model_config = ConfigDict(extra="forbid")

    plan: CodeGenerationPlan = Field(
        ...,
        description="The authoritative generation plan used to produce these files",
    )
    generated_files: list[GeneratedFile] = Field(
        ...,
        min_length=1,
        max_length=MAX_FILES,
        description="List of verified generated files matching the plan manifest exactly",
    )
    total_files: int = Field(
        ...,
        ge=1,
        le=MAX_FILES,
        description="Total count of generated files",
    )
    total_size_bytes: int = Field(
        ...,
        ge=1,
        le=MAX_TOTAL_SIZE_BYTES,
        description="Aggregate size of all generated files in bytes",
    )
    summary: str = Field(
        ...,
        min_length=10,
        description="Engineering summary of the scaffold implementation",
    )
