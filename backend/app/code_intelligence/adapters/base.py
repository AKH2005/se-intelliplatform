"""Base Language Adapter Interface for Polyglot Code Intelligence (Phase 14).

Defines the contract for language-specific parsers, symbol extractors, and dependency resolvers.
All adapters must isolate parse failures and return normalized CodeFile representations.
"""

from abc import ABC, abstractmethod
import hashlib
import logging
from typing import Any

from app.code_intelligence.contracts import (
    AuthorityClassification,
    CodeDependencyEdge,
    CodeDiagnostic,
    CodeExport,
    CodeFile,
    CodeImport,
    CodeLanguage,
    CodeSymbol,
    DependencyRelation,
)
from app.code_intelligence.detector import LanguageDetector

logger = logging.getLogger(__name__)


class BaseLanguageAdapter(ABC):
    """Abstract base class for all language-specific intelligence adapters."""

    @property
    @abstractmethod
    def language(self) -> CodeLanguage:
        """The primary CodeLanguage supported by this adapter."""
        pass

    def detect(self, file_path: str, content: str | None = None) -> bool:
        """Check if this adapter supports the given file."""
        return LanguageDetector.detect(file_path, content) == self.language

    def safe_parse(self, file_path: str, content: str) -> CodeFile:
        """Parse with fail-safe isolation, guaranteeing an intact CodeFile is returned even on syntax errors."""
        norm_path = file_path.replace("\\", "/").strip("/")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        is_test = LanguageDetector.is_test_file(norm_path)

        try:
            code_file = self.parse(norm_path, content)
            code_file.content_hash = content_hash
            code_file.is_test_file = is_test
            return code_file
        except Exception as exc:
            logger.warning(f"Parse error in {self.language.value} adapter for {norm_path}: {exc}")
            diag = CodeDiagnostic(
                file_path=norm_path,
                language=self.language,
                error_type="PARSE_FAILURE",
                message=f"Parser failure in {self.language.value} adapter: {exc}",
                severity="ERROR",
            )
            return CodeFile(
                file_path=norm_path,
                language=self.language,
                is_test_file=is_test,
                content_hash=content_hash,
                has_syntax_error=True,
                diagnostics=[diag],
            )

    @abstractmethod
    def parse(self, file_path: str, content: str) -> CodeFile:
        """Execute deterministic language parsing and extract symbols, imports, and exports."""
        pass

    @abstractmethod
    def resolve_internal_dependencies(
        self,
        source_file: str,
        imports: list[CodeImport],
        all_files: list[str],
    ) -> list[CodeDependencyEdge]:
        """Resolve imports from source_file against all existing project file paths."""
        pass
