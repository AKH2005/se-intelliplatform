"""Language Adapter Registry for Polyglot Code Intelligence (Phase 14).

Manages registration and lookup of language-specific code intelligence adapters.
Allows seamless addition of new language adapters without altering core engines.
"""

import logging
from typing import Any

from app.code_intelligence.adapters.base import BaseLanguageAdapter
from app.code_intelligence.adapters.java_adapter import JavaLanguageAdapter
from app.code_intelligence.adapters.javascript_adapter import JavaScriptLanguageAdapter
from app.code_intelligence.adapters.polyglot_adapter import PolyglotLanguageAdapter
from app.code_intelligence.adapters.python_adapter import PythonLanguageAdapter
from app.code_intelligence.adapters.typescript_adapter import TypeScriptLanguageAdapter
from app.code_intelligence.contracts import CodeLanguage
from app.code_intelligence.detector import LanguageDetector

logger = logging.getLogger(__name__)


class LanguageAdapterRegistry:
    """Central registry of deterministic language adapters."""

    def __init__(self, register_defaults: bool = True) -> None:
        self._adapters: dict[CodeLanguage, BaseLanguageAdapter] = {}
        if register_defaults:
            # Core primary AST/lexical adapters
            self.register(PythonLanguageAdapter())
            self.register(JavaScriptLanguageAdapter())
            self.register(TypeScriptLanguageAdapter())
            self.register(JavaLanguageAdapter())

            # Polyglot compiled & scripting languages
            for lang in (
                CodeLanguage.GO,
                CodeLanguage.RUST,
                CodeLanguage.CSHARP,
                CodeLanguage.C,
                CodeLanguage.CPP,
                CodeLanguage.PHP,
                CodeLanguage.RUBY,
                CodeLanguage.KOTLIN,
                CodeLanguage.SWIFT,
                CodeLanguage.SQL,
                CodeLanguage.HTML,
                CodeLanguage.CSS,
                CodeLanguage.JSON,
                CodeLanguage.YAML,
            ):
                self.register(PolyglotLanguageAdapter(lang))

    def register(self, adapter: BaseLanguageAdapter) -> None:
        """Register or override an adapter for a given language."""
        self._adapters[adapter.language] = adapter
        logger.debug(f"Registered language adapter for {adapter.language.value}.")

    def get_adapter(self, language: CodeLanguage) -> BaseLanguageAdapter | None:
        """Retrieve adapter registered for language, or None if unsupported."""
        return self._adapters.get(language)

    def get_adapter_for_file(self, file_path: str, content: str | None = None) -> BaseLanguageAdapter | None:
        """Detect language and return the corresponding adapter."""
        lang = LanguageDetector.detect(file_path, content)
        return self.get_adapter(lang)

    def supported_languages(self) -> list[CodeLanguage]:
        """List all currently supported languages."""
        return sorted(list(self._adapters.keys()), key=lambda l: l.value)


# Global default instance
_default_registry: LanguageAdapterRegistry | None = None


def get_default_registry() -> LanguageAdapterRegistry:
    """Obtain or initialize the singleton language adapter registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = LanguageAdapterRegistry(register_defaults=True)
    return _default_registry
