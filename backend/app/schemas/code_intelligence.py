"""Pydantic Request and Response Schemas for Polyglot Code Intelligence (Phase 14)."""

from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.code_intelligence.contracts import (
    CodeDependencyEdge,
    CodeDiagnostic,
    CodeExport,
    CodeFile,
    CodeImport,
    CodeLanguage,
    CodeSymbol,
    PolyglotDependencyGraph,
    TechnologyDetection,
)


class LanguageInventoryResponse(BaseModel):
    """Inventory of detected languages and file distribution across a project."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID
    total_files: int = Field(..., ge=0)
    counts: dict[str, int] = Field(default_factory=dict)
    percentages: dict[str, float] = Field(default_factory=dict)
    supported_languages: list[str] = Field(default_factory=list)


class CodeIntelligenceSummaryResponse(BaseModel):
    """High-level summary metrics of polyglot code analysis."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID
    version_id: uuid.UUID | None = None
    version_number: int | None = None
    total_files: int = Field(..., ge=0)
    total_symbols: int = Field(..., ge=0)
    total_edges: int = Field(..., ge=0)
    total_diagnostics: int = Field(..., ge=0)
    language_breakdown: dict[str, int] = Field(default_factory=dict)
    unresolved_imports_count: int = Field(default=0, ge=0)
    uncertain_dependencies_count: int = Field(default=0, ge=0)
    analyzed_at: datetime


class DependencyGraphResponse(BaseModel):
    """Complete or filtered polyglot dependency graph for a project."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID
    files_count: int
    edges_count: int
    forward_adjacency: dict[str, list[str]]
    reverse_adjacency: dict[str, list[str]]
    language_breakdown: dict[str, int]
    unresolved_imports: list[str]
    uncertain_dependencies: list[dict[str, Any]]
    diagnostics_count: int


class FileCodeIntelligenceResponse(BaseModel):
    """Detailed code intelligence findings for a single source file."""

    model_config = ConfigDict(extra="forbid")

    file_path: str
    language: CodeLanguage
    is_test_file: bool
    content_hash: str
    symbols: list[CodeSymbol]
    imports: list[CodeImport]
    exports: list[CodeExport]
    dependencies: list[CodeDependencyEdge]
    diagnostics: list[CodeDiagnostic]
    has_syntax_error: bool
    has_dynamic_constructs: bool


class ProjectTechnologiesResponse(BaseModel):
    """Detected programming languages, web technologies, and database technologies."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID
    technologies: list[TechnologyDetection] = Field(default_factory=list)
