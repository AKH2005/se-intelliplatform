"""Deterministic JavaScript Language Adapter for Polyglot Code Intelligence (Phase 14).

Parses JavaScript (.js, .jsx, .mjs, .cjs) source files using deterministic lexical
tokenization and structural pattern extraction. Extracts ES modules, CommonJS imports,
functions, classes, methods, exports, and relative project dependencies.
"""

import logging
import os
import re
from typing import Any

from pygments.lexers import JavascriptLexer
from pygments.token import Token

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
from app.code_intelligence.lexical_scanner import LexicalScanner

logger = logging.getLogger(__name__)


class JavaScriptLanguageAdapter(BaseLanguageAdapter):
    """Authoritative deterministic adapter for JavaScript and JSX code."""

    def __init__(self) -> None:
        self.lexer = JavascriptLexer()
        self.scanner = LexicalScanner()

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.JAVASCRIPT

    def parse(self, file_path: str, content: str) -> CodeFile:
        """Parse JavaScript source code and extract symbols, imports, and exports."""
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        exports: list[CodeExport] = []
        diagnostics: list[CodeDiagnostic] = []
        has_dynamic = False

        # Phase 14 Remediation: Lexical & Structural Scanning
        # 1. Mask comments and non-import string literals with whitespace (preserving offsets & lines)
        sanitized_content = self.scanner.mask_non_code_regions(content, self.language)
        # 2. Mask generic type parameter clauses in declaration headers (e.g. <T extends Base>)
        struct_content = self.scanner.mask_declaration_generics(sanitized_content)

        lines = content.splitlines()

        # 1. Regex patterns for ES Modules and CommonJS imports
        # import defaultExport from "module";
        # import * as name from "module";
        # import { export1, export2 as alias } from "module";
        # import "module";
        es_import_pattern = re.compile(
            r"""import\s+(?:(?P<default>[\w$]+)\s*,?\s*)?(?:(?:\*\s+as\s+(?P<namespace>[\w$]+))|(?P<named>\{[^}]+\}))?\s*(?:from\s*)?['"](?P<module>[^'"]+)['"]\s*;?""",
            re.MULTILINE,
        )

        # const foo = require('bar');
        # const { a, b } = require('bar');
        cjs_require_pattern = re.compile(
            r"""(?:const|let|var)\s+(?:(?P<single>[\w$]+)|(?P<destructured>\{[^}]+\}))\s*=\s*require\(\s*['"](?P<module>[^'"]+)['"]\s*\)""",
            re.MULTILINE,
        )

        # Dynamic require: require(variable)
        dynamic_require_pattern = re.compile(r"""require\(\s*(?!['"])(?P<expr>[^)]+)\)""")

        # Dynamic import: import('...') or import(variable)
        dynamic_import_pattern = re.compile(r"""import\(\s*(?P<expr>[^)]+)\)""")

        # 2. Extract ES Imports
        for match in es_import_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            mod = match.group("module")
            named_raw = match.group("named")
            default_name = match.group("default")
            namespace_name = match.group("namespace")

            imported_syms: list[str] = []
            if default_name:
                imported_syms.append(default_name)
            if namespace_name:
                imported_syms.append(f"* as {namespace_name}")
            if named_raw:
                # clean { foo, bar as b }
                clean_named = named_raw.strip("{}").split(",")
                for n in clean_named:
                    s = n.strip()
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

        # 3. Extract CommonJS requires
        for match in cjs_require_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            mod = match.group("module")
            single = match.group("single")
            destructured = match.group("destructured")

            imported_syms = []
            if single:
                imported_syms.append(single)
            if destructured:
                for item in destructured.strip("{}").split(","):
                    s = item.strip()
                    if s:
                        imported_syms.append(s.split(":")[0].strip())

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

        # 4. Extract Dynamic Imports & Dynamic Requires
        for match in dynamic_import_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            raw_expr = match.group("expr").strip("'\" ")
            has_dynamic = True
            imports.append(
                CodeImport(
                    module=raw_expr or "<dynamic>",
                    is_dynamic=True,
                    is_relative=raw_expr.startswith("./") or raw_expr.startswith("../"),
                    line_number=line_no,
                    raw_statement=content[match.start() : match.end()].strip(),
                )
            )
            diagnostics.append(
                CodeDiagnostic(
                    file_path=file_path,
                    language=self.language,
                    error_type="DYNAMIC_IMPORT",
                    line=line_no,
                    message="Dynamic import() expression detected.",
                    unsupported_construct=content[match.start() : match.end()].strip(),
                    severity="WARNING",
                )
            )

        for match in dynamic_require_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            has_dynamic = True
            diagnostics.append(
                CodeDiagnostic(
                    file_path=file_path,
                    language=self.language,
                    error_type="DYNAMIC_REQUIRE",
                    line=line_no,
                    message="Dynamic require(variable) expression detected.",
                    unsupported_construct=content[match.start() : match.end()].strip(),
                    severity="WARNING",
                )
            )

        # 5. Dangerous constructs: eval(...) or Function(...)
        eval_pattern = re.compile(r"""\b(?:eval|Function)\s*\(""")
        for match in eval_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            has_dynamic = True
            diagnostics.append(
                CodeDiagnostic(
                    file_path=file_path,
                    language=self.language,
                    error_type="DYNAMIC_CODE_EXECUTION",
                    line=line_no,
                    message="Dynamic code evaluation (eval / Function constructor) detected.",
                    unsupported_construct="eval/Function",
                    severity="WARNING",
                )
            )

        # 6. Extract Functions & Arrow Functions
        # function foo(...) or async function foo(...)
        func_pattern = re.compile(
            r"""(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(?P<name>[\w$]+)\s*\((?P<params>[^)]*)\)""",
            re.MULTILINE,
        )
        for match in func_pattern.finditer(struct_content):
            name = match.group("name")
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_exp = "export" in match.group(0)
            symbols.append(
                CodeSymbol(
                    name=name,
                    kind=SymbolKind.FUNCTION,
                    qualified_name=name,
                    line_number=line_no,
                    language=self.language,
                    is_exported=is_exp,
                    signature=f"({match.group('params').strip()})",
                )
            )

        # const/let foo = (...) => ... or const foo = function(...)
        arrow_pattern = re.compile(
            r"""(?:export\s+)?(?:const|let|var)\s+(?P<name>[\w$]+)\s*=\s*(?:async\s+)?(?:\((?P<params>[^)]*)\)|(?P<single_param>[\w$]+))\s*=>""",
            re.MULTILINE,
        )
        for match in arrow_pattern.finditer(struct_content):
            name = match.group("name")
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_exp = "export" in match.group(0)
            params = match.group("params") or match.group("single_param") or ""
            symbols.append(
                CodeSymbol(
                    name=name,
                    kind=SymbolKind.FUNCTION,
                    qualified_name=name,
                    line_number=line_no,
                    language=self.language,
                    is_exported=is_exp,
                    signature=f"({params.strip()})",
                )
            )

        # 6b. Extract Exported Variables / Constants (e.g. export const API_URL = ...)
        var_pattern = re.compile(
            r"""export\s+(?:const|let|var)\s+(?P<name>[\w$]+)\s*=""",
            re.MULTILINE,
        )
        for match in var_pattern.finditer(struct_content):
            name = match.group("name")
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            if not any(s.name == name for s in symbols):
                symbols.append(
                    CodeSymbol(
                        name=name,
                        kind=SymbolKind.VARIABLE,
                        qualified_name=name,
                        line_number=line_no,
                        language=self.language,
                        is_exported=True,
                    )
                )

        # 7. Extract Classes and Methods
        class_pattern = re.compile(
            r"""(?:export\s+)?(?:default\s+)?class\s+(?P<name>[\w$]+)(?:\s+extends\s+(?P<super>[\w$]+))?(?:\s+implements\s+(?P<implements>[\w$.,\s]+))?\s*\{""",
            re.MULTILINE,
        )
        for match in class_pattern.finditer(struct_content):
            c_name = match.group("name")
            super_name = match.group("super")
            implements_raw = match.group("implements")
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_exp = "export" in match.group(0)
            symbols.append(
                CodeSymbol(
                    name=c_name,
                    kind=SymbolKind.CLASS,
                    qualified_name=c_name,
                    line_number=line_no,
                    language=self.language,
                    is_exported=is_exp,
                )
            )

            # Record inheritance if present
            if super_name:
                clean_super = self.scanner.strip_type_parameters(super_name)
                if clean_super:
                    symbols.append(
                        CodeSymbol(
                            name=clean_super,
                            kind=SymbolKind.CLASS,
                            qualified_name=clean_super,
                            line_number=line_no,
                            language=self.language,
                            is_exported=is_exp,
                            parent_symbol=c_name,
                            signature="extends",
                        )
                    )

            # Record implements if present
            if implements_raw:
                for iface in self.scanner.split_balanced(implements_raw):
                    clean_iface = self.scanner.strip_type_parameters(iface)
                    if clean_iface:
                        symbols.append(
                            CodeSymbol(
                                name=clean_iface,
                                kind=SymbolKind.INTERFACE,
                                qualified_name=clean_iface,
                                line_number=line_no,
                                language=self.language,
                                is_exported=is_exp,
                                parent_symbol=c_name,
                                signature="implements",
                            )
                        )

            # Extract methods inside class definition using structural braces
            block_start = match.end()
            bracket_count = 1
            idx = block_start
            while idx < len(struct_content) and bracket_count > 0:
                if struct_content[idx] == "{":
                    bracket_count += 1
                elif struct_content[idx] == "}":
                    bracket_count -= 1
                idx += 1
            class_body = struct_content[block_start : idx - 1]

            method_pattern = re.compile(
                r"""(?:async\s+)?(?:static\s+)?(?P<name>[\w$]+)\s*\((?P<params>[^)]*)\)\s*\{""",
                re.MULTILINE,
            )
            for m_match in method_pattern.finditer(class_body):
                m_name = m_match.group("name")
                if m_name in ("if", "for", "while", "switch", "catch"):
                    continue
                m_pos = block_start + m_match.start()
                m_line = content[:m_pos].count("\n") + 1
                symbols.append(
                    CodeSymbol(
                        name=m_name,
                        kind=SymbolKind.CONSTRUCTOR if m_name == "constructor" else SymbolKind.METHOD,
                        qualified_name=f"{c_name}.{m_name}",
                        line_number=m_line,
                        language=self.language,
                        is_exported=is_exp,
                        parent_symbol=c_name,
                        signature=f"({m_match.group('params').strip()})",
                    )
                )

        # 8. Extract Exports
        # export default foo;
        export_default_pattern = re.compile(
            r"""export\s+default\s+(?:class\s+|function\s+)?(?P<name>[\w$]+)?""",
            re.MULTILINE,
        )
        for match in export_default_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            name = match.group("name") or "default"
            exports.append(
                CodeExport(
                    name=name,
                    is_default=True,
                    line_number=line_no,
                )
            )

        # export { a, b as c };
        export_named_pattern = re.compile(r"""export\s+\{([^}]+)\}\s*;?""", re.MULTILINE)
        for match in export_named_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            for item in match.group(1).split(","):
                s = item.strip()
                if s:
                    exp_name = s.split(" as ")[-1].strip()
                    exports.append(
                        CodeExport(
                            name=exp_name,
                            is_default=False,
                            line_number=line_no,
                        )
                    )

        # module.exports = ... or exports.foo = ...
        cjs_export_pattern = re.compile(
            r"""(?:module\.)?exports(?:\.(?P<named>[\w$]+))?\s*=\s*(?P<val>[^;\n]+)""",
            re.MULTILINE,
        )
        for match in cjs_export_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            named = match.group("named")
            exports.append(
                CodeExport(
                    name=named or "default",
                    is_default=named is None,
                    line_number=line_no,
                )
            )

        # Also register any symbols explicitly marked is_exported
        for s in symbols:
            if s.is_exported and s.parent_symbol is None:
                if not any(e.name == s.name for e in exports):
                    exports.append(
                        CodeExport(
                            name=s.name,
                            symbol_kind=s.kind,
                            line_number=s.line_number,
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

    def resolve_internal_dependencies(
        self,
        source_file: str,
        imports: list[CodeImport],
        all_files: list[str],
    ) -> list[CodeDependencyEdge]:
        """Resolve JavaScript/JSX relative imports against project file tree."""
        edges: list[CodeDependencyEdge] = []
        normalized_files = [f.replace("\\", "/").strip("/") for f in all_files]
        file_set = set(normalized_files)
        source_dir = os.path.dirname(source_file).replace("\\", "/")

        for imp in imports:
            if imp.is_dynamic or imp.module == "<dynamic>":
                edges.append(
                    CodeDependencyEdge(
                        source_file=source_file,
                        target_file="<dynamic>",
                        relation=DependencyRelation.DYNAMIC_IMPORT,
                        authority=AuthorityClassification.DYNAMIC,
                        line_number=imp.line_number,
                        is_resolved=False,
                        notes="Dynamic import call cannot be statically resolved.",
                    )
                )
                continue

            raw_mod = imp.module

            # If not relative, it's external (e.g. 'react', 'lodash', 'axios')
            if not imp.is_relative and not raw_mod.startswith("./") and not raw_mod.startswith("../"):
                edges.append(
                    CodeDependencyEdge(
                        source_file=source_file,
                        target_file=raw_mod,
                        relation=DependencyRelation.IMPORT,
                        authority=AuthorityClassification.UNRESOLVED,
                        line_number=imp.line_number,
                        is_resolved=False,
                        notes=f"External package '{raw_mod}'.",
                    )
                )
                continue

            # Resolve relative import
            norm_target_base = os.path.normpath(os.path.join(source_dir, raw_mod)).replace("\\", "/")

            resolved_path: str | None = None
            # Check exact match or with common JS/TS extensions: .js, .jsx, .ts, .tsx
            candidates = [
                norm_target_base,
                f"{norm_target_base}.js",
                f"{norm_target_base}.jsx",
                f"{norm_target_base}.ts",
                f"{norm_target_base}.tsx",
                f"{norm_target_base}/index.js",
                f"{norm_target_base}/index.jsx",
                f"{norm_target_base}/index.ts",
                f"{norm_target_base}/index.tsx",
            ]

            for cand in candidates:
                if cand in file_set:
                    resolved_path = cand
                    break

            if resolved_path and resolved_path != source_file:
                edges.append(
                    CodeDependencyEdge(
                        source_file=source_file,
                        target_file=resolved_path,
                        relation=DependencyRelation.IMPORT,
                        symbol=", ".join(imp.imported_symbols) if imp.imported_symbols else None,
                        authority=AuthorityClassification.DETERMINISTIC,
                        line_number=imp.line_number,
                        is_resolved=True,
                    )
                )
            else:
                edges.append(
                    CodeDependencyEdge(
                        source_file=source_file,
                        target_file=raw_mod,
                        relation=DependencyRelation.IMPORT,
                        authority=AuthorityClassification.UNRESOLVED,
                        line_number=imp.line_number,
                        is_resolved=False,
                        notes=f"Unresolved relative module '{raw_mod}'.",
                    )
                )

        return edges
