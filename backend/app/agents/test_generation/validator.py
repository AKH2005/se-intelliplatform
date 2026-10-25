"""Deterministic Safety, Quality, and Traceability Validator for AI-Generated Tests."""

import ast
import logging
import re
from typing import Any
from app.agents.contracts import ValidationResult
from app.agents.test_generation.contracts import (
    MAX_INDIVIDUAL_TEST_CODE_BYTES,
    MAX_TESTS,
    MAX_TOTAL_TEST_CODE_BYTES,
    AITestSuiteCandidate,
    GeneratedTest,
    GeneratedTestCandidate,
    TestCategory,
    TestGenerationInput,
)

logger = logging.getLogger(__name__)

# Sensitive filesystem indicators
FORBIDDEN_PATH_SUBSTRINGS: list[str] = [
    ".env",
    ".git",
    "docker-compose",
    "dockerfile",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "shadow",
    "passwd",
    "__pycache__",
]

# Forbidden import modules in generated test code
FORBIDDEN_IMPORT_MODULES: set[str] = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "requests",
    "urllib",
    "http",
    "aiohttp",
    "httpx",
    "pty",
    "commands",
    "importlib",
    "inspect",
    "pickle",
    "ctypes",
    "multiprocessing",
    "threading",
    "posix",
    "nt",
    "signal",
}

# Forbidden function calls / builtins
FORBIDDEN_CALL_NAMES: set[str] = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "globals",
    "locals",
    "getattr",
    "setattr",
    "delattr",
    "input",
    "exit",
    "quit",
}

# Forbidden attribute calls
FORBIDDEN_ATTRIBUTES: set[str] = {
    "system",
    "popen",
    "spawn",
    "fork",
    "remove",
    "unlink",
    "rmdir",
    "chmod",
    "environ",
    "connect",
    "send",
    "recv",
    "bind",
    "listen",
    "Popen",
    "check_output",
}

# Secret detection patterns
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("PRIVATE_KEY", re.compile(r"-----BEGIN\s+(?:RSA|OPENSSH|DSA|EC)?\s*PRIVATE\s+KEY-----", re.IGNORECASE)),
    ("AWS_KEY", re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}")),
    ("GITHUB_TOKEN", re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}")),
    ("GENERIC_API_KEY", re.compile(r"""(?:api[_-]?key|secret[_-]?key|auth[_-]?token)\s*[:=]\s*['"][A-Za-z0-9_\-]{20,}['"]""", re.IGNORECASE)),
    ("JWT_TOKEN", re.compile(r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*")),
]


class AITestValidator:
    """Authoritative, deterministic safety, quality, and anti-hallucination validator for AI-generated tests."""

    @classmethod
    def validate(
        cls,
        candidate: AITestSuiteCandidate,
        analysis_input: TestGenerationInput,
    ) -> ValidationResult:
        """Execute complete deterministic validation pipeline against candidate test suite."""
        errors: list[str] = []

        # 1. Suite-level bounds
        if not candidate.tests:
            return ValidationResult(is_valid=False, errors=["Test suite candidate contains no test cases."])

        if len(candidate.tests) > MAX_TESTS:
            errors.append(f"Test suite exceeds maximum allowed tests ({len(candidate.tests)} > {MAX_TESTS}).")

        # 2. Duplicate detection
        seen_test_ids: set[str] = set()
        seen_test_names: set[str] = set()
        total_code_bytes = 0

        for idx, test in enumerate(candidate.tests):
            prefix = f"Test #{idx + 1} ('{test.test_id or test.name}')"

            # If model swapped python function name into test_id and title into name, normalize safely
            if not re.match(r"^test_[a-zA-Z0-9_]+$", test.name) and re.match(r"^test_[a-zA-Z0-9_]+$", test.test_id):
                alt_name = test.test_id
                test.test_id = f"TEST-{idx + 1:03d}"
                test.name = alt_name

            # Check ID uniqueness
            if not test.test_id or not test.test_id.strip():
                errors.append(f"{prefix}: test_id cannot be blank.")
            elif test.test_id in seen_test_ids:
                errors.append(f"{prefix}: Duplicate test_id '{test.test_id}'.")
            else:
                seen_test_ids.add(test.test_id)

            # Check Name uniqueness and format
            if not test.name or not test.name.strip():
                errors.append(f"{prefix}: test name cannot be blank.")
            elif not re.match(r"^test_[a-zA-Z0-9_]+$", test.name):
                errors.append(f"{prefix}: Test name '{test.name}' must begin with 'test_' and contain only alphanumeric characters or underscores.")
            elif test.name in seen_test_names:
                errors.append(f"{prefix}: Duplicate test name '{test.name}'.")
            else:
                seen_test_names.add(test.name)

            # Check category
            try:
                TestCategory(test.category)
            except ValueError:
                errors.append(f"{prefix}: Invalid test category '{test.category}'. Allowed: {[c.value for c in TestCategory]}.")

            # Check target file path security and manifest existence
            path_err = cls._validate_target_path(test.target_file, analysis_input.manifest)
            if path_err:
                errors.append(f"{prefix}: {path_err}")

            # Check requirement traceability
            if test.requirement_ids and analysis_input.available_requirement_ids:
                for req_id in test.requirement_ids:
                    if req_id not in analysis_input.available_requirement_ids:
                        errors.append(f"{prefix}: Hallucinated requirement_id '{req_id}'. Not found in project requirements.")

            # Check code size limits
            code_bytes = len(test.code.encode("utf-8"))
            total_code_bytes += code_bytes
            if code_bytes > MAX_INDIVIDUAL_TEST_CODE_BYTES:
                errors.append(f"{prefix}: Test code size ({code_bytes} bytes) exceeds limit ({MAX_INDIVIDUAL_TEST_CODE_BYTES} bytes).")

            # Check secrets
            for sec_name, sec_regex in SECRET_PATTERNS:
                if sec_regex.search(test.code):
                    errors.append(f"{prefix}: Detected potential secret or credential pattern '{sec_name}'.")

            # 3. Deterministic AST Security and Quality Inspection
            ast_errors = cls._validate_test_ast(test.code, test.name)
            for a_err in ast_errors:
                errors.append(f"{prefix}: {a_err}")

        # Total code size check
        if total_code_bytes > MAX_TOTAL_TEST_CODE_BYTES:
            errors.append(f"Total test code size ({total_code_bytes} bytes) exceeds maximum limit ({MAX_TOTAL_TEST_CODE_BYTES} bytes).")

        return ValidationResult(is_valid=(len(errors) == 0), errors=errors)

    @classmethod
    def _validate_target_path(cls, path: str, manifest: list[str]) -> str | None:
        """Validate target file path against security rules and manifest."""
        if not path or not path.strip():
            return "target_file cannot be blank."

        cleaned = path.strip()
        if "\\" in cleaned:
            return f"Path contains backslashes: '{path}'. Only forward slashes are permitted."
        if cleaned.startswith(("/", "\\")):
            return f"Absolute paths are forbidden: '{path}'."
        if re.match(r"^[a-zA-Z]:", cleaned):
            return f"Windows drive paths are forbidden: '{path}'."
        if ".." in cleaned.split("/"):
            return f"Directory traversal ('..') is forbidden: '{path}'."

        lower_path = cleaned.lower()
        for forbidden in FORBIDDEN_PATH_SUBSTRINGS:
            if forbidden in lower_path:
                return f"Path references sensitive or forbidden file: '{path}'."

        if manifest and cleaned not in manifest:
            return f"Target file '{path}' not found in project manifest: {manifest}."

        return None

    @classmethod
    def _validate_test_ast(cls, code: str, expected_name: str) -> list[str]:
        """Inspect Python AST for syntax validity, security violations, and quality assertions."""
        errors: list[str] = []

        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            return [f"Python syntax error in test code: {se.msg} (line {se.lineno})"]

        has_function = False
        has_assertion = False
        has_executable_body = False

        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in FORBIDDEN_IMPORT_MODULES:
                        errors.append(f"Forbidden import '{alias.name}' detected. Test code must not access {root_mod}.")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in FORBIDDEN_IMPORT_MODULES:
                        errors.append(f"Forbidden import from '{node.module}' detected. Test code must not access {root_mod}.")

            # Check calls
            if isinstance(node, ast.Call):
                # Simple function call: name(...)
                if isinstance(node.func, ast.Name):
                    if node.func.id in FORBIDDEN_CALL_NAMES:
                        errors.append(f"Forbidden function call '{node.func.id}()' detected.")
                # Attribute call: obj.attr(...)
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in FORBIDDEN_ATTRIBUTES:
                        errors.append(f"Forbidden attribute call '.{node.func.attr}()' detected.")
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id in {"os", "subprocess", "socket", "sys"}:
                            errors.append(f"Forbidden access to '{node.func.value.id}.{node.func.attr}()'.")

                # Check for pytest.raises or assertion calls
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in {"raises", "approx", "warns"}:
                        has_assertion = True
                    elif node.func.attr.startswith("assert"):
                        has_assertion = True

            # Check Assert statement
            if isinstance(node, ast.Assert):
                has_assertion = True
                # Trivial assert check: assert True or assert 1 == 1
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    errors.append("Trivial assertion 'assert True' is not a meaningful test.")

            # Check FunctionDef
            if isinstance(node, ast.FunctionDef):
                has_function = True
                # Inspect statements in body
                body_statements = [stmt for stmt in node.body if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Constant)]
                if body_statements:
                    has_executable_body = True
                else:
                    errors.append(f"Test function '{node.name}' has no executable statements (empty or docstring only).")

        if not has_function:
            errors.append(f"Test code must define at least one test function (e.g. 'def {expected_name}():').")

        if not has_assertion:
            errors.append("Test code must contain at least one meaningful assertion ('assert' statement or 'pytest.raises').")

        return errors

    @classmethod
    def compile_candidate_to_suite(
        cls,
        candidate: AITestSuiteCandidate,
        analysis_input: TestGenerationInput,
        raw_metadata: dict[str, Any] | None = None,
    ) -> "AITestSuite":
        """Transform a validated candidate into an authoritative AITestSuite with executable test files."""
        from app.agents.test_generation.contracts import AITestSuite, GeneratedTest, TestCategory

        validated_tests: list[GeneratedTest] = []
        traceability_map: dict[str, list[str]] = {}

        for c_test in candidate.tests:
            gt = GeneratedTest(
                test_id=c_test.test_id,
                name=c_test.name,
                description=c_test.description,
                category=TestCategory(c_test.category),
                target_file=c_test.target_file,
                target_symbol=c_test.target_symbol,
                requirement_ids=c_test.requirement_ids,
                architecture_component=c_test.architecture_component,
                rationale=c_test.rationale,
                code=c_test.code.strip(),
                expected_behavior=c_test.expected_behavior,
            )
            validated_tests.append(gt)

            for req in gt.requirement_ids:
                if req not in traceability_map:
                    traceability_map[req] = []
                traceability_map[req].append(gt.test_id)

        # Assemble unified test file
        test_file_content = cls._generate_test_file_content(validated_tests)
        test_files = {"tests/test_ai_generated.py": test_file_content}

        return AITestSuite(
            project_id=analysis_input.project_id,
            workflow_execution_id=analysis_input.workflow_execution_id,
            summary=candidate.summary,
            tests=validated_tests,
            test_count=len(validated_tests),
            requirement_traceability=traceability_map,
            source_artifact_reference="code_generation",
            static_analysis_reference=analysis_input.static_analysis_result.result_id if analysis_input.static_analysis_result else None,
            test_files=test_files,
            metadata=raw_metadata or {},
        )

    @classmethod
    def _generate_test_file_content(cls, tests: list[GeneratedTest]) -> str:
        """Combine individual validated test snippets into a clean, runnable pytest module."""
        lines = [
            '"""AI-Generated Test Suite for Project Verification."""',
            "",
            "import pytest",
            "",
        ]

        for t in tests:
            lines.append(f"# Test ID: {t.test_id} [{t.category.value}]")
            lines.append(f"# Description: {t.description}")
            lines.append(f"# Target: {t.target_file} -> {t.target_symbol or 'module'}")
            lines.append(t.code)
            lines.append("")

        return "\n".join(lines)
