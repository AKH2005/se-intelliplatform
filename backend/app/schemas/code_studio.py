"""Pydantic Contracts and DTOs for Code Studio and File Operations."""

import enum
import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class FileNodeType(str, enum.Enum):
    """Classification of filesystem tree node."""

    FILE = "file"
    DIRECTORY = "directory"


class FileNode(BaseModel):
    """Hierarchical node representing a file or directory in the project tree."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique node identifier (relative path)")
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Normalized relative path from project root")
    type: FileNodeType = Field(..., description="'file' or 'directory'")
    size_bytes: int | None = Field(default=None, description="Size in bytes for files")
    language: str | None = Field(default=None, description="Inferred language or file type")
    children: list["FileNode"] | None = Field(
        default=None,
        description="Nested child nodes for directory nodes",
    )


class FileTreeResponse(BaseModel):
    """Hierarchical file tree representation of a project version."""

    model_config = ConfigDict(extra="ignore")

    project_id: uuid.UUID = Field(..., description="Project UUID")
    version_id: uuid.UUID | None = Field(default=None, description="Active or target version UUID")
    version_number: int | None = Field(default=None, description="Version number")
    has_generated_code: bool = Field(..., description="True if files exist for this project")
    total_files: int = Field(default=0, ge=0, description="Total number of files in tree")
    root_nodes: list[FileNode] = Field(default_factory=list, description="Top-level nodes")


class FileContentResponse(BaseModel):
    """Full source content and metadata for an individual project file."""

    model_config = ConfigDict(extra="ignore")

    path: str = Field(..., description="Normalized project-relative file path")
    name: str = Field(..., description="Base filename")
    language: str = Field(default="plaintext", description="Inferred programming language")
    content: str = Field(..., description="UTF-8 source text content")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    version_id: uuid.UUID = Field(..., description="Version UUID where this file resides")
    version_number: int = Field(..., ge=1, description="Version number")
    content_hash: str = Field(..., description="SHA-256 hash of file content")


class SaveFileRequest(BaseModel):
    """Request payload to safely edit and save a file, creating a child version."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., max_length=1_048_576, description="New source code content (max 1MB)")
    parent_version_id: uuid.UUID = Field(
        ...,
        description="Version UUID that the editor loaded (for optimistic concurrency protection)",
    )
    expected_content_hash: str | None = Field(
        default=None,
        description="Optional SHA-256 hash of existing file content to detect concurrent edits",
    )
    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Optional justification or commit message for the change",
    )


class ValidationStageOutcome(BaseModel):
    """Validation outcome for file save operation."""

    model_config = ConfigDict(extra="ignore")

    stage: str = Field(default="syntax_validation", description="Validation stage identifier")
    status: str = Field(..., description="'PASSED', 'FAILED', or 'SKIPPED'")
    message: str = Field(..., description="Human-readable outcome summary")
    errors: list[str] = Field(default_factory=list, description="Validation error details if any")
    warnings: list[str] = Field(default_factory=list, description="Validation warning details if any")


class SaveFileResponse(BaseModel):
    """Outcome of a successful authenticated file save operation."""

    model_config = ConfigDict(extra="ignore")

    success: bool = Field(..., description="True if save and version creation succeeded")
    project_id: uuid.UUID = Field(..., description="Project UUID")
    version_id: uuid.UUID = Field(..., description="New immutable child version UUID")
    version_number: int = Field(..., ge=1, description="New version number")
    parent_version_id: uuid.UUID = Field(..., description="Preceding version UUID")
    path: str = Field(..., description="Normalized relative path of edited file")
    size_bytes: int = Field(..., ge=0, description="New size of edited file")
    content_hash: str = Field(..., description="New SHA-256 hash of edited file")
    version_content_hash: str = Field(..., description="SHA-256 hash of entire version")
    validation: ValidationStageOutcome = Field(..., description="Validation outcome")
    message: str = Field(..., description="Status summary message")
