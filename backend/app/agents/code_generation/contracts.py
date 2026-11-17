"""Contracts, Data Models, and Conservative Limits for Code Generation Architecture."""

import enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# 1. Conservative Platform Limits
# ==============================================================================

MAX_FILES: int = 30
MAX_PATH_LENGTH: int = 150
MAX_FILE_SIZE_BYTES: int = 1024 * 1024  # 1 MB per file
MAX_TOTAL_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB total project size

SUPPORTED_LANGUAGES: set[str] = {"python", "typescript", "javascript", "polyglot"}
SUPPORTED_FRAMEWORKS: set[str] = {"fastapi", "react", "react+fastapi", "fullstack-react-fastapi"}
SUPPORTED_DATABASES: set[str] = {"postgresql", "sqlite", "in-memory"}
SUPPORTED_PACKAGE_MANAGERS: set[str] = {"pip", "npm", "yarn", "pnpm", "npm+pip"}


def is_fullstack_project(
    context: Any,
    architecture_recommendation: Any | None = None,
) -> bool:
    """Determine deterministically whether a project context requires a full-stack scaffold."""
    if not context or not getattr(context, "project", None):
        return False

    # 1. Project name, description, or slug explicitly references UI, web, or platform template archetypes
    p_text = f"{context.project.name} {context.project.description or ''} {getattr(context.project, 'slug', '') or ''}".lower()
    fullstack_keywords = [
        "react", "frontend", "fullstack", "full-stack", "web app", "task manager",
        "game", "arcade", "canvas", "dashboard", "portal", "store", "ecommerce",
        "catalog", "booking", "directory", "roster", "ui", "kanban", "snake",
    ]
    if any(k in p_text for k in fullstack_keywords):
        return True

    # 2. Canonical requirements indicate web UI, rendering, or frontend controls
    req_keywords = [
        "web interface", "dashboard", "react", "frontend", "ui", "browser",
        "canvas", "rendering", "controls", "touchpad", "screen", "web",
    ]
    for r in getattr(context, "requirements", []):
        r_text = f"{getattr(r, 'title', '')} {getattr(r, 'description', '')}".lower()
        if any(k in r_text for k in req_keywords):
            return True

    # 3. Upstream architecture recommendation includes FRONTEND category or React
    if architecture_recommendation:
        if isinstance(architecture_recommendation, dict):
            techs = architecture_recommendation.get("technologies", [])
            for t in techs:
                cat = t.get("category", "") if isinstance(t, dict) else getattr(t, "category", "")
                t_name = (t.get("technology", "") if isinstance(t, dict) else getattr(t, "technology", "")).lower()
                if cat == "FRONTEND" or "react" in t_name:
                    return True
        elif hasattr(architecture_recommendation, "technologies") and architecture_recommendation.technologies:
            for t in architecture_recommendation.technologies:
                cat = t.category.value if hasattr(t.category, "value") else str(t.category)
                if cat == "FRONTEND" or "react" in t.technology.lower():
                    return True

    return False


# ==============================================================================
# 2. Enumerations
# ==============================================================================

class ApplicationComplexityLevel(str, enum.Enum):
    """Complexity classification for application generation."""

    BASIC = "BASIC"       # Level 1: Portfolio, calculator, simple task list, informational site
    MEDIUM = "MEDIUM"     # Level 2: Primary target - multi-view, connected workflows, db persistence
    ADVANCED = "ADVANCED" # Level 3: Large enterprise, multiplayer, distributed systems


def classify_application_complexity(
    name: str = "",
    desc: str = "",
    requirements: list[Any] | None = None,
) -> ApplicationComplexityLevel:
    """Classify application scope into Basic (Level 1), Medium (Level 2), or Advanced (Level 3)."""
    combined = f"{name} {desc}".lower()
    req_texts = " ".join(
        f"{getattr(r, 'title', '')} {getattr(r, 'description', '')}".lower()
        for r in (requirements or [])
    )
    all_text = f"{combined} {req_texts}"

    # Level 3: Advanced
    advanced_keywords = [
        "multiplayer", "distributed", "microservices", "blockchain", "large enterprise",
        "federated", "real-time synchronization cluster", "streaming analytics platform",
    ]
    if any(k in all_text for k in advanced_keywords):
        return ApplicationComplexityLevel.ADVANCED

    # Level 1: Basic (isolated simple utility or single static page)
    basic_keywords = [
        "calculator", "simple portfolio", "personal portfolio", "simple counter",
        "basic task list", "static website", "informational website", "landing page only",
    ]
    is_basic = any(k in all_text for k in basic_keywords)
    has_medium_domain = any(
        m in all_text for m in [
            "ecommerce", "e-commerce", "inventory", "lms", "learning management",
            "hospital", "booking", "store", "eventhub", "management system", "game", "platform"
        ]
    )
    if is_basic and not has_medium_domain:
        return ApplicationComplexityLevel.BASIC

    # Default to Level 2: Medium (Primary Quality Target)
    return ApplicationComplexityLevel.MEDIUM


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
    complexity_level: ApplicationComplexityLevel = Field(
        default=ApplicationComplexityLevel.MEDIUM,
        description="Target complexity level (BASIC, MEDIUM, ADVANCED)",
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
    complexity_level: str = Field(default="MEDIUM")
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
    complexity_level: ApplicationComplexityLevel = Field(
        default=ApplicationComplexityLevel.MEDIUM,
        description="Target complexity level of the generated implementation",
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
