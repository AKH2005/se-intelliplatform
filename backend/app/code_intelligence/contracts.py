"""Unified Code Intelligence Model and Contracts for Phase 14 Polyglot Analysis.

Provides normalized intermediate representation (IR) across all supported programming languages:
Python, JavaScript, TypeScript, Java, and extensible language targets.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TechnologyCategory(str, Enum):
    """Categorical classification of software technologies."""
    PROGRAMMING_LANGUAGE = "PROGRAMMING_LANGUAGE"
    WEB_TECHNOLOGY = "WEB_TECHNOLOGY"
    DATABASE_ENGINE = "DATABASE_ENGINE"
    DATABASE_DIALECT = "DATABASE_DIALECT"


class DatabaseParadigm(str, Enum):
    """Architectural classification of databases."""
    RELATIONAL = "RELATIONAL"
    DOCUMENT = "DOCUMENT"
    KEY_VALUE = "KEY_VALUE"
    GRAPH = "GRAPH"


class CodeLanguage(str, Enum):
    """Categorical classification of supported source code languages and formats."""

    # Core general-purpose languages
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    KOTLIN = "kotlin"
    SWIFT = "swift"

    # Web & structural formats
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    JSON = "json"
    YAML = "yaml"

    # Database query languages / dialects
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"

    UNKNOWN = "unknown"


class TechnologyCapability(BaseModel):
    """Honest capabilities matrix for a specific technology."""
    model_config = ConfigDict(extra="ignore")

    can_detect: bool = True
    can_syntax_highlight: bool = True
    can_inspect_source: bool = True
    can_ast_analyze: bool = False
    can_dependency_analyze: bool = False
    can_generate_code: bool = False
    can_execute: bool = False
    can_live_preview: bool = False


class TechnologyDetection(BaseModel):
    """Deterministic detection report for a project language, tool, or database."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Display name of detected technology")
    category: TechnologyCategory = Field(..., description="Classification category")
    paradigm: DatabaseParadigm | None = Field(default=None, description="Database paradigm if applicable")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detection confidence score")
    evidence: list[str] = Field(default_factory=list, description="Concrete evidence justifying detection")
    detected_frameworks: list[str] = Field(default_factory=list, description="Detected frameworks and libraries")
    detected_drivers: list[str] = Field(default_factory=list, description="Detected database drivers and adapters")
    file_paths: list[str] = Field(default_factory=list, description="Associated file paths")
    capabilities: TechnologyCapability = Field(default_factory=TechnologyCapability, description="Active capability matrix")
    schema_info: dict[str, Any] | None = Field(default=None, description="Extracted schema structure if available")


def get_technology_category(lang: CodeLanguage) -> TechnologyCategory:
    """Classify a CodeLanguage into its authoritative TechnologyCategory."""
    if lang in (
        CodeLanguage.PYTHON,
        CodeLanguage.JAVASCRIPT,
        CodeLanguage.TYPESCRIPT,
        CodeLanguage.JAVA,
        CodeLanguage.C,
        CodeLanguage.CPP,
        CodeLanguage.CSHARP,
        CodeLanguage.GO,
        CodeLanguage.RUST,
        CodeLanguage.PHP,
        CodeLanguage.RUBY,
        CodeLanguage.KOTLIN,
        CodeLanguage.SWIFT,
    ):
        return TechnologyCategory.PROGRAMMING_LANGUAGE
    elif lang in (
        CodeLanguage.HTML,
        CodeLanguage.CSS,
        CodeLanguage.SQL,
        CodeLanguage.JSON,
        CodeLanguage.YAML,
    ):
        return TechnologyCategory.WEB_TECHNOLOGY
    elif lang in (
        CodeLanguage.MYSQL,
        CodeLanguage.POSTGRESQL,
        CodeLanguage.SQLITE,
        CodeLanguage.MONGODB,
    ):
        return TechnologyCategory.DATABASE_DIALECT
    return TechnologyCategory.PROGRAMMING_LANGUAGE


def get_honest_capabilities(lang: CodeLanguage) -> TechnologyCapability:
    """Report genuine, un-fabricated capabilities for a technology."""
    if lang == CodeLanguage.PYTHON:
        return TechnologyCapability(
            can_detect=True,
            can_syntax_highlight=True,
            can_inspect_source=True,
            can_ast_analyze=True,
            can_dependency_analyze=True,
            can_generate_code=True,
            can_execute=True,
            can_live_preview=True,
        )
    elif lang in (CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT):
        return TechnologyCapability(
            can_detect=True,
            can_syntax_highlight=True,
            can_inspect_source=True,
            can_ast_analyze=True,
            can_dependency_analyze=True,
            can_generate_code=True,
            can_execute=True,
            can_live_preview=True,
        )
    elif lang == CodeLanguage.JAVA:
        return TechnologyCapability(
            can_detect=True,
            can_syntax_highlight=True,
            can_inspect_source=True,
            can_ast_analyze=True,
            can_dependency_analyze=True,
            can_generate_code=True,
            can_execute=False,
            can_live_preview=False,
        )
    elif lang in (CodeLanguage.GO, CodeLanguage.RUST, CodeLanguage.CSHARP):
        return TechnologyCapability(
            can_detect=True,
            can_syntax_highlight=True,
            can_inspect_source=True,
            can_ast_analyze=False,
            can_dependency_analyze=True,
            can_generate_code=True,
            can_execute=False,
            can_live_preview=False,
        )
    elif lang in (CodeLanguage.C, CodeLanguage.CPP, CodeLanguage.PHP, CodeLanguage.RUBY, CodeLanguage.KOTLIN, CodeLanguage.SWIFT):
        return TechnologyCapability(
            can_detect=True,
            can_syntax_highlight=True,
            can_inspect_source=True,
            can_ast_analyze=False,
            can_dependency_analyze=True,
            can_generate_code=False,
            can_execute=False,
            can_live_preview=False,
        )
    elif lang in (CodeLanguage.HTML, CodeLanguage.CSS):
        return TechnologyCapability(
            can_detect=True,
            can_syntax_highlight=True,
            can_inspect_source=True,
            can_ast_analyze=False,
            can_dependency_analyze=False,
            can_generate_code=True,
            can_execute=False,
            can_live_preview=True,
        )
    elif lang == CodeLanguage.SQL:
        return TechnologyCapability(
            can_detect=True,
            can_syntax_highlight=True,
            can_inspect_source=True,
            can_ast_analyze=False,
            can_dependency_analyze=False,
            can_generate_code=True,
            can_execute=False,
            can_live_preview=False,
        )
    else:
        return TechnologyCapability(
            can_detect=True,
            can_syntax_highlight=True,
            can_inspect_source=True,
            can_ast_analyze=False,
            can_dependency_analyze=False,
            can_generate_code=False,
            can_execute=False,
            can_live_preview=False,
        )


class SymbolKind(str, Enum):
    """Normalized symbol categories across programming languages."""

    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    CLASS = "CLASS"
    INTERFACE = "INTERFACE"
    TYPE_ALIAS = "TYPE_ALIAS"
    VARIABLE = "VARIABLE"
    PACKAGE = "PACKAGE"
    MODULE = "MODULE"
    CONSTRUCTOR = "CONSTRUCTOR"
    ENUM = "ENUM"
    PROPERTY = "PROPERTY"


class DependencyRelation(str, Enum):
    """Classification of code dependency relationships across languages."""

    IMPORT = "IMPORT"
    FROM_IMPORT = "FROM_IMPORT"
    DYNAMIC_IMPORT = "DYNAMIC_IMPORT"
    CALL = "CALL"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    TYPE_REFERENCE = "TYPE_REFERENCE"
    REQUIRE = "REQUIRE"
    EXPORT = "EXPORT"
    TEST_TARGET = "TEST_TARGET"
    UNKNOWN = "UNKNOWN"


class AuthorityClassification(str, Enum):
    """Deterministic authority and certainty classification of code intelligence findings."""

    DETERMINISTIC = "DETERMINISTIC"
    INFERRED = "INFERRED"
    UNRESOLVED = "UNRESOLVED"
    UNSUPPORTED = "UNSUPPORTED"
    DYNAMIC = "DYNAMIC"


class CodeDiagnostic(BaseModel):
    """Structured diagnostic generated during language parsing or dependency extraction."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(..., description="Project-relative normalized file path")
    language: CodeLanguage = Field(..., description="Detected file language")
    error_type: str = Field(..., description="Classification (e.g. SYNTAX_ERROR, DYNAMIC_CONSTRUCT, UNRESOLVED_IMPORT)")
    line: int | None = Field(default=None, description="Line number where diagnostic occurred")
    column: int | None = Field(default=None, description="Column offset if available")
    message: str = Field(..., description="Human-readable diagnostic description")
    unsupported_construct: str | None = Field(default=None, description="Raw syntax or construct that triggered diagnostic")
    severity: str = Field(default="WARNING", description="Severity level: ERROR, WARNING, INFO")

    @field_validator("file_path", mode="before")
    @classmethod
    def normalize_file_path(cls, v: Any) -> str:
        return str(v).replace("\\", "/").strip("/")


class CodeSymbol(BaseModel):
    """Normalized symbol representation (class, function, interface, method, etc.)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Symbol identifier name")
    kind: SymbolKind = Field(..., description="Symbol category")
    qualified_name: str = Field(..., description="Namespace or container-qualified identifier")
    line_number: int = Field(..., ge=1, description="Source line number where symbol is declared")
    column: int | None = Field(default=None, description="Source column offset")
    language: CodeLanguage = Field(..., description="Language defining this symbol")
    is_exported: bool = Field(default=False, description="True if symbol is exported from file/module")
    signature: str | None = Field(default=None, description="Optional normalized parameter/return signature")
    docstring: str | None = Field(default=None, description="Optional extracted documentation comment")
    parent_symbol: str | None = Field(default=None, description="Enclosing class/module name if nested")


class CodeImport(BaseModel):
    """Normalized representation of an external or internal module import."""

    model_config = ConfigDict(extra="forbid")

    module: str = Field(..., description="Import module path or package name")
    imported_symbols: list[str] = Field(default_factory=list, description="Specific imported symbol names")
    alias: str | None = Field(default=None, description="Optional local alias identifier")
    is_dynamic: bool = Field(default=False, description="True if import is dynamically evaluated at runtime")
    is_relative: bool = Field(default=False, description="True if import is a relative project path (./, ../)")
    line_number: int = Field(default=1, ge=1, description="Source line number of import statement")
    raw_statement: str | None = Field(default=None, description="Original source statement string")


class CodeExport(BaseModel):
    """Normalized representation of a symbol exported for external consumption."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Exported symbol or alias name")
    symbol_kind: SymbolKind | None = Field(default=None, description="Underlying symbol kind if determinable")
    is_default: bool = Field(default=False, description="True if this is the default module export")
    line_number: int = Field(default=1, ge=1, description="Line number of export statement")


class CodeDependencyEdge(BaseModel):
    """Directed dependency relationship: source_file depends on target_file."""

    model_config = ConfigDict(extra="forbid")

    source_file: str = Field(..., description="Dependent file path")
    target_file: str = Field(..., description="Dependency file path")
    relation: DependencyRelation = Field(default=DependencyRelation.IMPORT, description="Nature of relationship")
    symbol: str | None = Field(default=None, description="Referenced symbol name if specific")
    authority: AuthorityClassification = Field(
        default=AuthorityClassification.DETERMINISTIC,
        description="Confidence/authority classification of this edge",
    )
    line_number: int = Field(default=1, ge=1, description="Line number in source file establishing dependency")
    is_resolved: bool = Field(default=True, description="True if target_file points to an existing project file")
    notes: str | None = Field(default=None, description="Diagnostic commentary on edge resolution")

    @field_validator("source_file", "target_file", mode="before")
    @classmethod
    def normalize_paths(cls, v: Any) -> str:
        return str(v).replace("\\", "/").strip("/")


class CodeFile(BaseModel):
    """Complete normalized code intelligence unit for a single source file."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(..., description="Project-relative normalized file path")
    language: CodeLanguage = Field(..., description="Detected file language")
    is_test_file: bool = Field(default=False, description="True if classified as a test file")
    content_hash: str = Field(default="", description="SHA-256 hash of file contents for incremental caching")
    symbols: list[CodeSymbol] = Field(default_factory=list, description="Extracted top-level and nested symbols")
    imports: list[CodeImport] = Field(default_factory=list, description="Import statements declared in file")
    exports: list[CodeExport] = Field(default_factory=list, description="Symbols exported from file")
    dependencies: list[CodeDependencyEdge] = Field(default_factory=list, description="Resolved outbound dependencies")
    diagnostics: list[CodeDiagnostic] = Field(default_factory=list, description="Parser or uncertainty diagnostics")
    has_syntax_error: bool = Field(default=False, description="True if file contained unparseable syntax")
    has_dynamic_constructs: bool = Field(default=False, description="True if dynamic execution/reflection was detected")

    @field_validator("file_path", mode="before")
    @classmethod
    def normalize_file_path(cls, v: Any) -> str:
        return str(v).replace("\\", "/").strip("/")


class PolyglotDependencyGraph(BaseModel):
    """Comprehensive multi-language dependency graph for an entire project."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(..., description="Canonical project UUID string")
    files: dict[str, CodeFile] = Field(default_factory=dict, description="Normalized file map keyed by relative path")
    edges: list[CodeDependencyEdge] = Field(default_factory=list, description="All directed dependency edges")
    forward_adjacency: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Forward index: file -> list of dependencies it imports",
    )
    reverse_adjacency: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Reverse index: file -> list of dependents that import it",
    )
    language_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="File count breakdown by language (e.g. {'python': 45, 'typescript': 30})",
    )
    unresolved_imports: list[str] = Field(
        default_factory=list,
        description="External or unresolvable imports identified across project",
    )
    uncertain_dependencies: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Records of dynamic imports, eval, reflection, or syntax issues causing uncertainty",
    )
    diagnostics: list[CodeDiagnostic] = Field(
        default_factory=list,
        description="Aggregated diagnostics across all project files",
    )
    total_symbols: int = Field(default=0, ge=0, description="Total extracted code symbols across all files")
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of graph computation",
    )
