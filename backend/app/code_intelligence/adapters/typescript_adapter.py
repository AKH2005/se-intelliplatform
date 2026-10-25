"""Deterministic TypeScript Language Adapter for Polyglot Code Intelligence (Phase 14).

Parses TypeScript (.ts, .tsx, .mts, .cts) source files, extracting interfaces,
types, enums, classes, methods, functions, type imports, and module dependencies.
Seamlessly cross-resolves imports with both TypeScript and JavaScript files.
"""

import logging
import os
import re
from typing import Any

from pygments.lexers import TypeScriptLexer

from app.code_intelligence.adapters.javascript_adapter import JavaScriptLanguageAdapter
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


class TypeScriptLanguageAdapter(JavaScriptLanguageAdapter):
    """Authoritative deterministic adapter for TypeScript and TSX code."""

    def __init__(self) -> None:
        super().__init__()
        self.ts_lexer = TypeScriptLexer()

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.TYPESCRIPT

    def parse(self, file_path: str, content: str) -> CodeFile:
        """Parse TypeScript source code, extending JS analysis with TS constructs."""
        # First obtain base JS extractions (imports, functions, classes, exports)
        base_file = super().parse(file_path, content)

        # Obtain masked structural content (comments & non-import strings masked, generics masked)
        sanitized_content = self.scanner.mask_non_code_regions(content, self.language)
        struct_content = self.scanner.mask_declaration_generics(sanitized_content)

        symbols = list(base_file.symbols)
        imports = list(base_file.imports)
        exports = list(base_file.exports)
        diagnostics = list(base_file.diagnostics)
        has_dynamic = base_file.has_dynamic_constructs

        # 1. Extract Type-Only Imports: import type { Foo, Bar } from './types';
        ts_type_import_pattern = re.compile(
            r"""import\s+type\s+(?:(?P<default>[\w$]+)\s*,?\s*)?(?:\{(?P<named>[^}]+)\})?\s*from\s*['"](?P<module>[^'"]+)['"]\s*;?""",
            re.MULTILINE,
        )
        for match in ts_type_import_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            mod = match.group("module")
            named_raw = match.group("named")
            default_name = match.group("default")

            imported_syms: list[str] = []
            if default_name:
                imported_syms.append(default_name)
            if named_raw:
                for item in named_raw.split(","):
                    s = item.strip()
                    if s:
                        imported_syms.append(s.split(" as ")[0].strip())

            is_rel = mod.startswith("./") or mod.startswith("../")
            imports.append(
                CodeImport(
                    module=mod,
                    imported_symbols=imported_syms,
                    is_dynamic=False,
                    is_relative=is_rel,
                    line_number=line_no,
                    raw_statement=content[match.start() : match.end()].strip(),
                )
            )

        # 2. Extract Interfaces: interface User { ... } or interface User extends BaseUser { ... }
        interface_pattern = re.compile(
            r"""(?:export\s+)?(?:default\s+)?interface\s+(?P<name>[\w$]+)(?:\s+extends\s+(?P<super>[\w$,\s]+))?\s*\{""",
            re.MULTILINE,
        )
        for match in interface_pattern.finditer(struct_content):
            name = match.group("name")
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_exp = "export" in match.group(0)

            symbols.append(
                CodeSymbol(
                    name=name,
                    kind=SymbolKind.INTERFACE,
                    qualified_name=name,
                    line_number=line_no,
                    language=self.language,
                    is_exported=is_exp,
                )
            )
            if is_exp and not any(e.name == name for e in exports):
                exports.append(
                    CodeExport(
                        name=name,
                        symbol_kind=SymbolKind.INTERFACE,
                        line_number=line_no,
                    )
                )

        # 3. Extract Type Aliases: type ID = string | number;
        type_alias_pattern = re.compile(
            r"""(?:export\s+)?type\s+(?P<name>[\w$]+)\s*=""",
            re.MULTILINE,
        )
        for match in type_alias_pattern.finditer(struct_content):
            name = match.group("name")
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_exp = "export" in match.group(0)

            symbols.append(
                CodeSymbol(
                    name=name,
                    kind=SymbolKind.TYPE_ALIAS,
                    qualified_name=name,
                    line_number=line_no,
                    language=self.language,
                    is_exported=is_exp,
                )
            )
            if is_exp and not any(e.name == name for e in exports):
                exports.append(
                    CodeExport(
                        name=name,
                        symbol_kind=SymbolKind.TYPE_ALIAS,
                        line_number=line_no,
                    )
                )

        # 4. Extract Enums: enum Status { ACTIVE, INACTIVE }
        enum_pattern = re.compile(
            r"""(?:export\s+)?(?:const\s+)?enum\s+(?P<name>[\w$]+)\s*\{""",
            re.MULTILINE,
        )
        for match in enum_pattern.finditer(struct_content):
            name = match.group("name")
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_exp = "export" in match.group(0)

            symbols.append(
                CodeSymbol(
                    name=name,
                    kind=SymbolKind.ENUM,
                    qualified_name=name,
                    line_number=line_no,
                    language=self.language,
                    is_exported=is_exp,
                )
            )
            if is_exp and not any(e.name == name for e in exports):
                exports.append(
                    CodeExport(
                        name=name,
                        symbol_kind=SymbolKind.ENUM,
                        line_number=line_no,
                    )
                )

        # 5. Extract TypeScript methods with visibility keywords (public, private, protected)
        ts_method_pattern = re.compile(
            r"""(?:public|private|protected|readonly)\s+(?:async\s+)?(?:static\s+)?(?P<name>[\w$]+)\s*\((?P<params>[^)]*)\)""",
            re.MULTILINE,
        )
        for match in ts_method_pattern.finditer(struct_content):
            m_name = match.group("name")
            if m_name in ("constructor", "if", "for", "while", "switch", "catch"):
                continue
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            if not any(s.name == m_name and s.line_number == line_no for s in symbols):
                symbols.append(
                    CodeSymbol(
                        name=m_name,
                        kind=SymbolKind.METHOD,
                        qualified_name=m_name,
                        line_number=line_no,
                        language=self.language,
                        signature=f"({match.group('params').strip()})",
                    )
                )

        return CodeFile(
            file_path=file_path,
            language=self.language,
            symbols=symbols,
            imports=imports,
            exports=exports,
            diagnostics=diagnostics,
            has_dynamic_constructs=has_dynamic,
        )
