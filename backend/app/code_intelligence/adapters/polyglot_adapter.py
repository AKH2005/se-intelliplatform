"""Polyglot Language Adapter for Phase 14 Polyglot Code Intelligence.

Deterministic parser and symbol extractor for Go, Rust, C#, C, C++, PHP,
Ruby, Kotlin, Swift, SQL, HTML, CSS, JSON, and YAML.
"""

import logging
import os
import re
from typing import Any

from app.code_intelligence.adapters.base import BaseLanguageAdapter
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
    SymbolKind,
)

logger = logging.getLogger(__name__)


class PolyglotLanguageAdapter(BaseLanguageAdapter):
    """Deterministic adapter for polyglot languages and web technologies."""

    def __init__(self, language: CodeLanguage) -> None:
        self._language = language

    @property
    def language(self) -> CodeLanguage:
        return self._language

    def parse(self, file_path: str, content: str) -> CodeFile:
        """Parse source content extracting symbols, imports, and exports."""
        norm_path = file_path.replace("\\", "/").strip("/")
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        exports: list[CodeExport] = []
        lines = content.splitlines()

        if self._language == CodeLanguage.GO:
            self._parse_go(norm_path, content, lines, symbols, imports, exports)
        elif self._language == CodeLanguage.RUST:
            self._parse_rust(norm_path, content, lines, symbols, imports, exports)
        elif self._language == CodeLanguage.CSHARP:
            self._parse_csharp(norm_path, content, lines, symbols, imports, exports)
        elif self._language in (CodeLanguage.C, CodeLanguage.CPP):
            self._parse_c_cpp(norm_path, content, lines, symbols, imports, exports)
        elif self._language == CodeLanguage.PHP:
            self._parse_php(norm_path, content, lines, symbols, imports, exports)
        elif self._language == CodeLanguage.RUBY:
            self._parse_ruby(norm_path, content, lines, symbols, imports, exports)
        elif self._language == CodeLanguage.KOTLIN:
            self._parse_kotlin(norm_path, content, lines, symbols, imports, exports)
        elif self._language == CodeLanguage.SWIFT:
            self._parse_swift(norm_path, content, lines, symbols, imports, exports)
        elif self._language == CodeLanguage.SQL:
            self._parse_sql(norm_path, content, lines, symbols, imports, exports)
        elif self._language in (CodeLanguage.HTML, CodeLanguage.CSS, CodeLanguage.JSON, CodeLanguage.YAML):
            self._parse_web(norm_path, content, lines, symbols, imports, exports)

        return CodeFile(
            file_path=norm_path,
            language=self._language,
            symbols=symbols,
            imports=imports,
            exports=exports,
            has_syntax_error=False,
        )

    def _parse_go(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            # Imports
            single_imp = re.match(r'^import\s+"([^"]+)"', s)
            if single_imp:
                spec = single_imp.group(1)
                imports.append(CodeImport(module_specifier=spec, imported_symbols=[], line_number=i))
            # Functions
            fn_match = re.match(r"^func\s+(?:\([^)]+\)\s*)?([A-Za-z0-9_]+)\s*\(", s)
            if fn_match:
                name = fn_match.group(1)
                is_pub = name[0].isupper()
                symbols.append(CodeSymbol(name=name, kind=SymbolKind.FUNCTION, line_start=i, line_end=i, is_exported=is_pub))
                if is_pub:
                    exports.append(CodeExport(symbol_name=name, is_default=False, line_number=i))
            # Structs & Interfaces
            type_match = re.match(r"^type\s+([A-Za-z0-9_]+)\s+(struct|interface)", s)
            if type_match:
                name = type_match.group(1)
                kind = SymbolKind.CLASS if type_match.group(2) == "struct" else SymbolKind.INTERFACE
                is_pub = name[0].isupper()
                symbols.append(CodeSymbol(name=name, kind=kind, line_start=i, line_end=i, is_exported=is_pub))
                if is_pub:
                    exports.append(CodeExport(symbol_name=name, is_default=False, line_number=i))

        # Multi-line imports: import ( ... )
        multi_imp = re.findall(r'import\s*\(([^)]+)\)', content)
        for block in multi_imp:
            for item in re.findall(r'"([^"]+)"', block):
                imports.append(CodeImport(module_specifier=item, imported_symbols=[]))

    def _parse_rust(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            # use statements
            use_match = re.match(r'^(?:pub\s+)?use\s+([^;]+);', s)
            if use_match:
                spec = use_match.group(1).strip()
                imports.append(CodeImport(module_specifier=spec, imported_symbols=[], line_number=i))
            # Struct, Enum, Trait
            type_match = re.match(r'^(pub\s+)?(struct|enum|trait)\s+([A-Za-z0-9_]+)', s)
            if type_match:
                is_pub = bool(type_match.group(1))
                name = type_match.group(3)
                kind = SymbolKind.INTERFACE if type_match.group(2) == "trait" else SymbolKind.CLASS
                symbols.append(CodeSymbol(name=name, kind=kind, line_start=i, line_end=i, is_exported=is_pub))
                if is_pub:
                    exports.append(CodeExport(symbol_name=name, is_default=False, line_number=i))
            # Functions
            fn_match = re.match(r'^(pub\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)', s)
            if fn_match:
                is_pub = bool(fn_match.group(1))
                name = fn_match.group(2)
                symbols.append(CodeSymbol(name=name, kind=SymbolKind.FUNCTION, line_start=i, line_end=i, is_exported=is_pub))
                if is_pub:
                    exports.append(CodeExport(symbol_name=name, is_default=False, line_number=i))

    def _parse_csharp(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            # using
            using_match = re.match(r'^using\s+([^;]+);', s)
            if using_match:
                imports.append(CodeImport(module_specifier=using_match.group(1).strip(), imported_symbols=[], line_number=i))
            # Class, Interface, Struct, Record
            type_match = re.match(r'^(?:public|internal|protected|private)?\s*(?:static|sealed|abstract)?\s*(class|interface|struct|record)\s+([A-Za-z0-9_]+)', s)
            if type_match:
                kind = SymbolKind.INTERFACE if type_match.group(1) == "interface" else SymbolKind.CLASS
                name = type_match.group(2)
                symbols.append(CodeSymbol(name=name, kind=kind, line_start=i, line_end=i, is_exported="public" in s))

    def _parse_c_cpp(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            # #include
            inc_match = re.match(r'^#include\s+["<]([^">]+)[">]', s)
            if inc_match:
                imports.append(CodeImport(module_specifier=inc_match.group(1), imported_symbols=[], line_number=i))
            # struct or class
            struct_match = re.match(r'^(?:class|struct)\s+([A-Za-z0-9_]+)', s)
            if struct_match:
                symbols.append(CodeSymbol(name=struct_match.group(1), kind=SymbolKind.CLASS, line_start=i, line_end=i, is_exported=True))

    def _parse_php(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            use_match = re.match(r'^use\s+([^;]+);', s)
            if use_match:
                imports.append(CodeImport(module_specifier=use_match.group(1).strip(), imported_symbols=[], line_number=i))
            class_match = re.match(r'^(?:final\s+|abstract\s+)?(class|interface|trait)\s+([A-Za-z0-9_]+)', s)
            if class_match:
                name = class_match.group(2)
                kind = SymbolKind.INTERFACE if class_match.group(1) == "interface" else SymbolKind.CLASS
                symbols.append(CodeSymbol(name=name, kind=kind, line_start=i, line_end=i, is_exported=True))
            fn_match = re.match(r'^(?:public\s+|protected\s+|private\s+)?function\s+([A-Za-z0-9_]+)\s*\(', s)
            if fn_match:
                symbols.append(CodeSymbol(name=fn_match.group(1), kind=SymbolKind.FUNCTION, line_start=i, line_end=i, is_exported=True))

    def _parse_ruby(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            req_match = re.match(r'^(?:require|require_relative)\s+[\'"]([^\'"]+)[\'"]', s)
            if req_match:
                imports.append(CodeImport(module_specifier=req_match.group(1), imported_symbols=[], line_number=i))
            class_match = re.match(r'^(?:class|module)\s+([A-Za-z0-9_:]+)', s)
            if class_match:
                symbols.append(CodeSymbol(name=class_match.group(1), kind=SymbolKind.CLASS, line_start=i, line_end=i, is_exported=True))
            def_match = re.match(r'^def\s+([A-Za-z0-9_!?.]+)', s)
            if def_match:
                symbols.append(CodeSymbol(name=def_match.group(1), kind=SymbolKind.FUNCTION, line_start=i, line_end=i, is_exported=True))

    def _parse_kotlin(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            imp_match = re.match(r'^import\s+([^\s;]+)', s)
            if imp_match:
                imports.append(CodeImport(module_specifier=imp_match.group(1), imported_symbols=[], line_number=i))
            class_match = re.match(r'^(?:open\s+|data\s+|sealed\s+)?(class|interface|object)\s+([A-Za-z0-9_]+)', s)
            if class_match:
                name = class_match.group(2)
                kind = SymbolKind.INTERFACE if class_match.group(1) == "interface" else SymbolKind.CLASS
                symbols.append(CodeSymbol(name=name, kind=kind, line_start=i, line_end=i, is_exported=True))
            fun_match = re.match(r'^fun\s+(?:<[^>]+>\s*)?([A-Za-z0-9_]+)\s*\(', s)
            if fun_match:
                symbols.append(CodeSymbol(name=fun_match.group(1), kind=SymbolKind.FUNCTION, line_start=i, line_end=i, is_exported=True))

    def _parse_swift(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            imp_match = re.match(r'^import\s+([^\s;]+)', s)
            if imp_match:
                imports.append(CodeImport(module_specifier=imp_match.group(1), imported_symbols=[], line_number=i))
            type_match = re.match(r'^(?:public\s+|open\s+)?(class|struct|protocol|enum)\s+([A-Za-z0-9_]+)', s)
            if type_match:
                name = type_match.group(2)
                kind = SymbolKind.INTERFACE if type_match.group(1) == "protocol" else SymbolKind.CLASS
                symbols.append(CodeSymbol(name=name, kind=kind, line_start=i, line_end=i, is_exported="public" in s or "open" in s))
            fn_match = re.match(r'^(?:public\s+|open\s+)?func\s+([A-Za-z0-9_]+)\s*\(', s)
            if fn_match:
                symbols.append(CodeSymbol(name=fn_match.group(1), kind=SymbolKind.FUNCTION, line_start=i, line_end=i, is_exported="public" in s or "open" in s))

    def _parse_sql(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        table_matches = re.finditer(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[`"]?[\w]+[`"]?\.)?[`"]?([A-Za-z0-9_]+)[`"]?', content, re.IGNORECASE)
        for m in table_matches:
            name = m.group(1)
            line_no = content[:m.start()].count("\n") + 1
            symbols.append(CodeSymbol(name=name, kind=SymbolKind.CLASS, line_start=line_no, line_end=line_no, is_exported=True))

        view_matches = re.finditer(r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:[`"]?[\w]+[`"]?\.)?[`"]?([A-Za-z0-9_]+)[`"]?', content, re.IGNORECASE)
        for m in view_matches:
            name = m.group(1)
            line_no = content[:m.start()].count("\n") + 1
            symbols.append(CodeSymbol(name=name, kind=SymbolKind.INTERFACE, line_start=line_no, line_end=line_no, is_exported=True))

    def _parse_web(self, file_path: str, content: str, lines: list[str], symbols: list[CodeSymbol], imports: list[CodeImport], exports: list[CodeExport]) -> None:
        # Detect CSS imports
        if self._language == CodeLanguage.CSS:
            for i, line in enumerate(lines, start=1):
                css_imp = re.match(r'@import\s+[\'"]([^\'"]+)[\'"]', line.strip())
                if css_imp:
                    imports.append(CodeImport(module_specifier=css_imp.group(1), imported_symbols=[], line_number=i))

    def resolve_internal_dependencies(
        self,
        source_file: str,
        imports: list[CodeImport],
        all_files: list[str],
    ) -> list[CodeDependencyEdge]:
        """Resolve imports against existing project files."""
        edges: list[CodeDependencyEdge] = []
        source_dir = os.path.dirname(source_file)

        for imp in imports:
            spec = imp.module_specifier.replace("\\", "/").strip()
            # Match directly or by basename
            matched_target: str | None = None
            for candidate in all_files:
                if candidate == spec or candidate.endswith("/" + spec):
                    matched_target = candidate
                    break
                # Try relative resolve
                rel_path = os.path.normpath(os.path.join(source_dir, spec)).replace("\\", "/")
                if candidate == rel_path or candidate.startswith(rel_path + "."):
                    matched_target = candidate
                    break

            if matched_target and matched_target != source_file:
                edges.append(
                    CodeDependencyEdge(
                        source_file=source_file,
                        target_file=matched_target,
                        relation=DependencyRelation.IMPORTS,
                        is_static=True,
                        authority=AuthorityClassification.DEFINITE,
                    )
                )

        return edges
