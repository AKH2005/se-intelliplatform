"""Deterministic Java Language Adapter for Polyglot Code Intelligence (Phase 14).

Parses Java (.java) source files extracting package declarations, imports,
classes, interfaces, records, enums, inheritance, interface implementations,
constructors, methods, and reflection constructs.
"""

import logging
import os
import re
from typing import Any

from pygments.lexers import JavaLexer

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

# Standard Java packages to avoid marking standard classes as internal
JAVA_STANDARD_PACKAGES: frozenset[str] = frozenset({
    "java",
    "javax",
    "sun",
    "com.sun",
    "jdk",
    "org.w3c",
    "org.xml",
    "org.ietf",
})


class JavaLanguageAdapter(BaseLanguageAdapter):
    """Authoritative deterministic adapter for Java source files."""

    def __init__(self) -> None:
        self.lexer = JavaLexer()
        self.scanner = LexicalScanner()

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.JAVA

    def parse(self, file_path: str, content: str) -> CodeFile:
        """Parse Java source code and extract symbols, imports, and exports."""
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        exports: list[CodeExport] = []
        diagnostics: list[CodeDiagnostic] = []
        has_dynamic = False

        # Phase 14 Remediation: Lexical & Structural Scanning
        # 1. Mask comments and string literals with whitespace (preserving offsets & lines)
        sanitized_content = self.scanner.mask_non_code_regions(content, self.language)
        # 2. Mask generic type parameter clauses in declaration headers (e.g. <T extends Base>)
        struct_content = self.scanner.mask_declaration_generics(sanitized_content)

        # 1. Extract Package Declaration: package com.example.service;
        package_name: str = ""
        pkg_match = re.search(r"""^\s*package\s+(?P<pkg>[\w.]+)\s*;""", struct_content, re.MULTILINE)
        if pkg_match:
            package_name = pkg_match.group("pkg").strip()
            line_no = content[:pkg_match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    name=package_name,
                    kind=SymbolKind.PACKAGE,
                    qualified_name=package_name,
                    line_number=line_no,
                    language=self.language,
                    is_exported=True,
                )
            )

        # 2. Extract Imports: import com.example.model.User; or import static ...;
        import_pattern = re.compile(
            r"""^\s*import\s+(?:static\s+)?(?P<import>[\w.*]+)\s*;""",
            re.MULTILINE,
        )
        for match in import_pattern.finditer(struct_content):
            raw_imp = match.group("import").strip()
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_wildcard = raw_imp.endswith(".*")
            target_class = raw_imp.split(".")[-1] if not is_wildcard else None

            imports.append(
                CodeImport(
                    module=raw_imp,
                    imported_symbols=[target_class] if target_class else ["*"],
                    is_dynamic=False,
                    is_relative=False,
                    line_number=line_no,
                    raw_statement=content[match.start() : match.end()].strip(),
                )
            )

        # 3. Detect Reflection and Dynamic Class Loading (only in genuine code)
        # Class.forName(...), .getDeclaredMethod(...), .newInstance(), .invoke(...)
        reflection_pattern = re.compile(
            r"""\b(?:Class\.forName|getDeclaredMethod|getMethod|getDeclaredField|getField|\.newInstance\(|\.invoke\()\b"""
        )
        for match in reflection_pattern.finditer(struct_content):
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            has_dynamic = True
            diagnostics.append(
                CodeDiagnostic(
                    file_path=file_path,
                    language=self.language,
                    error_type="REFLECTION_DETECTED",
                    line=line_no,
                    message=f"Java reflection invocation '{match.group(0)}' detected.",
                    unsupported_construct=content[match.start() : match.end()].strip(),
                    severity="WARNING",
                )
            )

        # 4. Extract Classes, Interfaces, Records, and Enums
        # public class UserService extends BaseService implements IUserService, IAuditable {
        type_def_pattern = re.compile(
            r"""(?:(?P<vis>public|protected|private)\s+)?(?:(?P<mod>abstract|final|static)\s+)*(?P<type>class|interface|record|enum)\s+(?P<name>[\w$]+)(?:\s+extends\s+(?P<extends>[\w$.]+))?(?:\s+implements\s+(?P<implements>[\w$.,\s]+))?\s*\{""",
            re.MULTILINE,
        )
        for match in type_def_pattern.finditer(struct_content):
            t_type = match.group("type")
            t_name = match.group("name")
            t_vis = match.group("vis") or "package"
            extends_raw = match.group("extends")
            implements_raw = match.group("implements")

            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_pub = t_vis == "public"

            kind_map = {
                "class": SymbolKind.CLASS,
                "interface": SymbolKind.INTERFACE,
                "record": SymbolKind.CLASS,
                "enum": SymbolKind.ENUM,
            }
            s_kind = kind_map.get(t_type, SymbolKind.CLASS)
            q_name = f"{package_name}.{t_name}" if package_name else t_name

            symbols.append(
                CodeSymbol(
                    name=t_name,
                    kind=s_kind,
                    qualified_name=q_name,
                    line_number=line_no,
                    language=self.language,
                    is_exported=is_pub,
                )
            )

            # Export public types
            if is_pub:
                exports.append(
                    CodeExport(
                        name=t_name,
                        symbol_kind=s_kind,
                        is_default=False,
                        line_number=line_no,
                    )
                )

            # Record extends and implements relationships (structurally stripped of generics)
            if extends_raw:
                clean_super = self.scanner.strip_type_parameters(extends_raw)
                if clean_super:
                    symbols.append(
                        CodeSymbol(
                            name=clean_super,
                            kind=SymbolKind.CLASS,
                            qualified_name=clean_super,
                            line_number=line_no,
                            language=self.language,
                            parent_symbol=t_name,
                            signature="extends",
                        )
                    )

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
                                parent_symbol=t_name,
                                signature="implements",
                            )
                        )

        # 5. Extract Constructors and Methods
        # public void doWork(...) { or public User findById(UUID id) {
        method_pattern = re.compile(
            r"""^\s*(?:(?P<vis>public|protected|private)\s+)?(?:(?P<mod>static|final|abstract|synchronized)\s+)*(?:(?P<ret>[\w$\[\]]+(?:\[\])?)\s+)?(?P<name>[\w$]+)\s*\((?P<params>[^)]*)\)\s*(?:throws\s+[\w$.,\s]+)?\s*\{""",
            re.MULTILINE,
        )
        for match in method_pattern.finditer(struct_content):
            name = match.group("name")
            if name in ("if", "for", "while", "switch", "catch", "synchronized"):
                continue
            ret = match.group("ret")
            start_pos = match.start()
            line_no = content[:start_pos].count("\n") + 1
            is_constructor = ret is None or ret.strip() == ""

            sym_name = f"{name}.<init>" if is_constructor else name
            symbols.append(
                CodeSymbol(
                    name=sym_name,
                    kind=SymbolKind.CONSTRUCTOR if is_constructor else SymbolKind.METHOD,
                    qualified_name=sym_name,
                    parent_symbol=name if is_constructor else None,
                    line_number=line_no,
                    language=self.language,
                    is_exported=(match.group("vis") == "public"),
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

    def resolve_internal_dependencies(
        self,
        source_file: str,
        imports: list[CodeImport],
        all_files: list[str],
    ) -> list[CodeDependencyEdge]:
        """Resolve Java imports against project .java files."""
        edges: list[CodeDependencyEdge] = []
        normalized_files = [f.replace("\\", "/").strip("/") for f in all_files if f.endswith(".java")]

        # Index project Java files by expected class name and package path
        # e.g., src/main/java/com/example/UserService.java -> (com.example.UserService, UserService)
        class_to_file: dict[str, str] = {}
        for f in normalized_files:
            base_class = os.path.splitext(os.path.basename(f))[0]
            class_to_file[base_class] = f
            # Also index by suffix path
            mod_suffix = f.replace("/", ".").replace(".java", "")
            class_to_file[mod_suffix] = f

        for imp in imports:
            raw_imp = imp.module
            # Skip JDK standard packages
            top_pkg = raw_imp.split(".")[0]
            if top_pkg in JAVA_STANDARD_PACKAGES:
                continue

            is_wildcard = raw_imp.endswith(".*")
            resolved_targets: list[str] = []

            if is_wildcard:
                pkg_prefix = raw_imp[:-2].replace(".", "/")
                for f in normalized_files:
                    if pkg_prefix in f:
                        resolved_targets.append(f)
            else:
                target_class = raw_imp.split(".")[-1]
                if target_class in class_to_file:
                    resolved_targets.append(class_to_file[target_class])
                else:
                    path_cand = raw_imp.replace(".", "/") + ".java"
                    for f in normalized_files:
                        if f.endswith(path_cand) or path_cand in f:
                            resolved_targets.append(f)

            if resolved_targets:
                for tgt in resolved_targets:
                    if tgt != source_file:
                        edges.append(
                            CodeDependencyEdge(
                                source_file=source_file,
                                target_file=tgt,
                                relation=DependencyRelation.IMPORT,
                                symbol=raw_imp.split(".")[-1] if not is_wildcard else "*",
                                authority=AuthorityClassification.DETERMINISTIC,
                                line_number=imp.line_number,
                                is_resolved=True,
                            )
                        )
            else:
                edges.append(
                    CodeDependencyEdge(
                        source_file=source_file,
                        target_file=raw_imp,
                        relation=DependencyRelation.IMPORT,
                        authority=AuthorityClassification.UNRESOLVED,
                        line_number=imp.line_number,
                        is_resolved=False,
                        notes=f"External Java package or library '{raw_imp}'.",
                    )
                )

        return edges
