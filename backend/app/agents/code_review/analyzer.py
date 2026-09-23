"""Deterministic Static Analyzer and In-Memory Secret Scanner for Code Review."""

import ast
import re
from app.agents.code_review.contracts import (
    CodeReviewFinding,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)

REDACTED_PLACEHOLDER = "***REDACTED_SECRET***"

# Compiled regex patterns for mandatory candidate secret detection
SECRET_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "AWS Access Key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "Potential exposed AWS Access Key ID detected.",
    ),
    (
        "Private Key Header",
        re.compile(r"-----BEGIN (?:[A-Z0-9_\-]+\s+)*KEY-----"),
        "Embedded cryptographic private key detected.",
    ),
    (
        "Bearer Token",
        re.compile(r"(?i)\bBearer\s+['\"]?([a-zA-Z0-9_\-\.]{20,})['\"]?"),
        "Hardcoded Bearer authentication token detected.",
    ),
    (
        "API Key Assignment",
        re.compile(
            r"(?i)\b(api_key|apikey|secret_key|access_token|auth_token)\s*=\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]"
        ),
        "Hardcoded API key or access token assignment detected.",
    ),
    (
        "Password Assignment",
        re.compile(
            r"(?i)\b(password|passwd|pwd)\s*=\s*['\"]([^'\"]{6,})['\"]"
        ),
        "Hardcoded credential or password assignment detected.",
    ),
    (
        "Connection String With Credentials",
        re.compile(
            r"(?i)\b(?:postgres|postgresql|mysql|mongodb|redis)://[^:\s]+:[^@\s]+@[^\s'\"]+"
        ),
        "Database or cache connection string with embedded credentials detected.",
    ),
]


class SecretScanner:
    """Deterministic, in-memory regex scanner for credentials and tokens.

    Ensures secrets are detected, flagged as CRITICAL security findings, and redacted
    before any prompt dispatch to language models. Never exposes or stores raw secrets.
    """

    @classmethod
    def scan_and_redact(
        cls, file_path: str, content: str
    ) -> tuple[str, list[CodeReviewFinding]]:
        """Scans content for secrets, returning (redacted_content, findings)."""
        findings: list[CodeReviewFinding] = []
        lines = content.splitlines()
        redacted_lines = list(lines)

        for line_idx, line in enumerate(lines, start=1):
            line_mutated = False
            for secret_name, pattern, desc in SECRET_PATTERNS:
                matches = list(pattern.finditer(line))
                if matches:
                    line_mutated = True
                    # Mask the secret in the line for redaction
                    for m in matches:
                        raw_matched = m.group(0)
                        redacted_lines[line_idx - 1] = redacted_lines[line_idx - 1].replace(
                            raw_matched, REDACTED_PLACEHOLDER
                        )

                    # Evidence shows the line with REDACTED_PLACEHOLDER, NEVER the raw secret
                    masked_evidence = redacted_lines[line_idx - 1].strip()
                    findings.append(
                        CodeReviewFinding(
                            finding_id=f"STATIC-SEC-{line_idx}",
                            file_path=file_path,
                            line_start=line_idx,
                            line_end=line_idx,
                            severity=FindingSeverity.CRITICAL,
                            category=FindingCategory.SECURITY,
                            source=FindingSource.STATIC_ANALYSIS,
                            title=f"Potential Secret Detected: {secret_name}",
                            description=(
                                f"{desc} Secrets should never be committed into source code. "
                                "Store credentials in environment variables or an external secrets vault."
                            ),
                            evidence=masked_evidence if masked_evidence else REDACTED_PLACEHOLDER,
                            recommendation="Remove the hardcoded secret immediately and rotate the compromised credential.",
                            rule_id="SECRET-DETECTION",
                        )
                    )

        redacted_content = "\n".join(redacted_lines)
        if content.endswith("\n") and not redacted_content.endswith("\n"):
            redacted_content += "\n"

        return redacted_content, findings


class PythonASTAnalyzer:
    """Deterministic, standard-library AST and structural analysis.

    Operates strictly on in-memory syntax trees. Never invokes compile(), eval(), or exec().
    """

    @classmethod
    def analyze(cls, file_path: str, content: str) -> list[CodeReviewFinding]:
        """Performs static syntax and AST pattern inspection on Python code."""
        findings: list[CodeReviewFinding] = []
        lines = content.splitlines()
        total_lines = len(lines) if lines else 1

        # 1. Syntax Check via ast.parse
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as syn_err:
            line_no = syn_err.lineno or 1
            safe_line = min(max(1, line_no), total_lines)
            evidence_line = lines[safe_line - 1].strip() if lines and safe_line <= len(lines) else "SyntaxError"

            findings.append(
                CodeReviewFinding(
                    finding_id=f"STATIC-SYN-{safe_line}",
                    file_path=file_path,
                    line_start=safe_line,
                    line_end=safe_line,
                    severity=FindingSeverity.CRITICAL,
                    category=FindingCategory.CORRECTNESS,
                    source=FindingSource.STATIC_ANALYSIS,
                    title="Syntax Error",
                    description=f"Python parser error: {syn_err.msg}",
                    evidence=evidence_line if evidence_line else "SyntaxError",
                    recommendation="Fix Python syntax error to permit valid module compilation.",
                    rule_id="AST-SYNTAX-ERROR",
                )
            )
            # If syntax is invalid, AST cannot be walked further
            return findings

        # 2. Structural & AST Pattern Checks
        findings.extend(cls._check_docstring(file_path, tree, lines))
        findings.extend(cls._walk_ast_rules(file_path, tree, lines))

        return findings

    @classmethod
    def _check_docstring(
        cls, file_path: str, tree: ast.AST, lines: list[str]
    ) -> list[CodeReviewFinding]:
        findings: list[CodeReviewFinding] = []
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        if len(non_empty_lines) >= 10:
            docstring = ast.get_docstring(tree)
            if not docstring:
                first_line = lines[0].strip() if lines else "file header"
                findings.append(
                    CodeReviewFinding(
                        finding_id="STATIC-DOC-1",
                        file_path=file_path,
                        line_start=1,
                        line_end=1,
                        severity=FindingSeverity.INFO,
                        category=FindingCategory.READABILITY,
                        source=FindingSource.STATIC_ANALYSIS,
                        title="Missing Module Docstring",
                        description="Substantial Python module lacks a top-level module docstring.",
                        evidence=first_line if first_line else "# Module start",
                        recommendation="Add a descriptive top-level module docstring explaining file purpose.",
                        rule_id="AST-MISSING-DOCSTRING",
                    )
                )
        return findings

    @classmethod
    def _walk_ast_rules(
        cls, file_path: str, tree: ast.AST, lines: list[str]
    ) -> list[CodeReviewFinding]:
        findings: list[CodeReviewFinding] = []

        for node in ast.walk(tree):
            line_no = getattr(node, "lineno", None)
            if line_no is None:
                continue

            safe_line = min(max(1, line_no), len(lines)) if lines else 1
            evidence_line = lines[safe_line - 1].strip() if lines else ""

            # Check for dynamic execution: eval()
            if isinstance(node, ast.Call):
                func = node.func
                # Direct call to eval or exec
                if isinstance(func, ast.Name):
                    if func.id == "eval":
                        findings.append(
                            CodeReviewFinding(
                                finding_id=f"STATIC-AST-{safe_line}",
                                file_path=file_path,
                                line_start=safe_line,
                                line_end=safe_line,
                                severity=FindingSeverity.HIGH,
                                category=FindingCategory.SECURITY,
                                source=FindingSource.STATIC_ANALYSIS,
                                title="Use of Dynamic Code Execution (eval)",
                                description="Calling eval() can lead to arbitrary code execution if evaluating untrusted inputs.",
                                evidence=evidence_line if evidence_line else "eval(...)",
                                recommendation="Replace eval() with safe alternatives like ast.literal_eval() or explicit parsers.",
                                rule_id="AST-EVAL",
                            )
                        )
                    elif func.id == "exec":
                        findings.append(
                            CodeReviewFinding(
                                finding_id=f"STATIC-AST-{safe_line}",
                                file_path=file_path,
                                line_start=safe_line,
                                line_end=safe_line,
                                severity=FindingSeverity.HIGH,
                                category=FindingCategory.SECURITY,
                                source=FindingSource.STATIC_ANALYSIS,
                                title="Use of Dynamic Code Execution (exec)",
                                description="Calling exec() executes arbitrary code strings and presents critical security risks.",
                                evidence=evidence_line if evidence_line else "exec(...)",
                                recommendation="Refactor to avoid dynamic code execution; use standard polymorphism or dispatch tables.",
                                rule_id="AST-EXEC",
                            )
                        )

                # Check for os.system
                elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == "os" and func.attr == "system":
                        findings.append(
                            CodeReviewFinding(
                                finding_id=f"STATIC-AST-{safe_line}",
                                file_path=file_path,
                                line_start=safe_line,
                                line_end=safe_line,
                                severity=FindingSeverity.HIGH,
                                category=FindingCategory.SECURITY,
                                source=FindingSource.STATIC_ANALYSIS,
                                title="Use of os.system()",
                                description="os.system() spawns a subshell and is vulnerable to shell command injection attacks.",
                                evidence=evidence_line if evidence_line else "os.system(...)",
                                recommendation="Use subprocess.run with shell=False and pass arguments as a list.",
                                rule_id="AST-OS-SYSTEM",
                            )
                        )
                    # Check for subprocess.*(..., shell=True)
                    elif func.value.id == "subprocess":
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                findings.append(
                                    CodeReviewFinding(
                                        finding_id=f"STATIC-AST-{safe_line}",
                                        file_path=file_path,
                                        line_start=safe_line,
                                        line_end=safe_line,
                                        severity=FindingSeverity.HIGH,
                                        category=FindingCategory.SECURITY,
                                        source=FindingSource.STATIC_ANALYSIS,
                                        title="Subprocess Executed with shell=True",
                                        description="Running subprocess commands with shell=True poses severe shell injection risks.",
                                        evidence=evidence_line if evidence_line else "shell=True",
                                        recommendation="Set shell=False and pass command and arguments as a sequence of strings.",
                                        rule_id="AST-SUBPROCESS-SHELL",
                                    )
                                )

            # Check for bare/empty except clauses
            elif isinstance(node, ast.ExceptHandler):
                if cls._is_empty_or_pass_body(node.body):
                    findings.append(
                        CodeReviewFinding(
                            finding_id=f"STATIC-AST-{safe_line}",
                            file_path=file_path,
                            line_start=safe_line,
                            line_end=safe_line,
                            severity=FindingSeverity.MEDIUM,
                            category=FindingCategory.ERROR_HANDLING,
                            source=FindingSource.STATIC_ANALYSIS,
                            title="Empty or Silenced Exception Handler",
                            description="Exception handler contains only pass or empty statement, swallowing errors without logging or handling.",
                            evidence=evidence_line if evidence_line else "except: pass",
                            recommendation="Log caught exceptions, specify concrete exception types, or add appropriate fallback handling.",
                            rule_id="AST-EMPTY-EXCEPT",
                        )
                    )

        # Check for excessive nesting
        findings.extend(cls._check_nesting(file_path, tree, lines))

        return findings

    @classmethod
    def _is_empty_or_pass_body(cls, body: list[ast.stmt]) -> bool:
        if not body:
            return True
        if len(body) == 1:
            stmt = body[0]
            if isinstance(stmt, ast.Pass):
                return True
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
                return True
        return False

    @classmethod
    def _check_nesting(
        cls, file_path: str, tree: ast.AST, lines: list[str]
    ) -> list[CodeReviewFinding]:
        findings: list[CodeReviewFinding] = []
        max_depth = 5

        def _traverse(node: ast.AST, current_depth: int) -> None:
            is_nesting_block = isinstance(
                node,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.Try,
                    ast.With,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            next_depth = current_depth + 1 if is_nesting_block else current_depth

            if is_nesting_block and next_depth >= max_depth:
                line_no = getattr(node, "lineno", 1)
                safe_line = min(max(1, line_no), len(lines)) if lines else 1
                evidence_line = lines[safe_line - 1].strip() if lines else ""
                findings.append(
                    CodeReviewFinding(
                        finding_id=f"STATIC-NEST-{safe_line}",
                        file_path=file_path,
                        line_start=safe_line,
                        line_end=safe_line,
                        severity=FindingSeverity.LOW,
                        category=FindingCategory.MAINTAINABILITY,
                        source=FindingSource.STATIC_ANALYSIS,
                        title="Excessive Nesting Depth",
                        description=f"Control flow exceeds nesting depth of {max_depth}, hindering readability and testability.",
                        evidence=evidence_line if evidence_line else "nested block",
                        recommendation="Refactor deeply nested blocks by extracting helper functions or applying guard clauses.",
                        rule_id="AST-EXCESSIVE-NESTING",
                    )
                )
                # Don't recurse deeper on the same chain to avoid duplicate reports
                return

            for child in ast.iter_child_nodes(node):
                _traverse(child, next_depth)

        _traverse(tree, 0)
        return findings
