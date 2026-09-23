"""Unit tests for Phase 8.1 SecretScanner and PythonASTAnalyzer."""

import pytest

from app.agents.code_review.analyzer import (
    REDACTED_PLACEHOLDER,
    PythonASTAnalyzer,
    SecretScanner,
)
from app.agents.code_review.contracts import (
    FindingCategory,
    FindingSeverity,
    FindingSource,
)


def test_secret_scanner_detects_aws_key():
    fake_aws_key = "AKIAIOSFODNN7EXAMPLE"
    code = f"AWS_KEY = '{fake_aws_key}'\nprint(AWS_KEY)\n"
    redacted, findings = SecretScanner.scan_and_redact("config.py", code)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "SECRET-DETECTION"
    assert f.severity == FindingSeverity.CRITICAL
    assert f.category == FindingCategory.SECURITY
    assert f.source == FindingSource.STATIC_ANALYSIS
    assert f.line_start == 1

    # Invariant: Raw secret must NOT be in redacted code or evidence
    assert fake_aws_key not in redacted
    assert REDACTED_PLACEHOLDER in redacted
    assert fake_aws_key not in f.evidence
    assert fake_aws_key not in f.description


def test_secret_scanner_detects_private_key_header():
    code = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----\n"
    redacted, findings = SecretScanner.scan_and_redact("key.pem", code)

    assert len(findings) >= 1
    f = findings[0]
    assert f.category == FindingCategory.SECURITY
    assert f.severity == FindingSeverity.CRITICAL
    assert "-----BEGIN RSA PRIVATE KEY-----" not in redacted
    assert REDACTED_PLACEHOLDER in redacted


def test_secret_scanner_detects_bearer_token():
    fake_token = "Bearer a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    code = f"auth_header = '{fake_token}'\n"
    redacted, findings = SecretScanner.scan_and_redact("client.py", code)

    assert len(findings) == 1
    assert "Bearer" in findings[0].title
    assert "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6" not in redacted
    assert REDACTED_PLACEHOLDER in redacted


def test_secret_scanner_detects_api_key_and_password():
    code = (
        "api_key = 'abcdef1234567890abcdef'\n"
        "password = 'super_secret_password'\n"
    )
    redacted, findings = SecretScanner.scan_and_redact("creds.py", code)

    assert len(findings) == 2
    assert "abcdef1234567890abcdef" not in redacted
    assert "super_secret_password" not in redacted
    assert REDACTED_PLACEHOLDER in redacted


def test_secret_scanner_detects_connection_string():
    code = "DB_URL = 'postgres://admin:secretpass123@db.example.com:5432/production'\n"
    redacted, findings = SecretScanner.scan_and_redact("db.py", code)

    assert len(findings) == 1
    assert "secretpass123" not in redacted
    assert REDACTED_PLACEHOLDER in redacted


def test_secret_scanner_clean_code():
    code = "def add(a, b):\n    return a + b\n"
    redacted, findings = SecretScanner.scan_and_redact("math.py", code)

    assert len(findings) == 0
    assert redacted == code


def test_ast_analyzer_clean_code():
    code = '"""Module docstring."""\n\ndef square(x: int) -> int:\n    return x * x\n'
    findings = PythonASTAnalyzer.analyze("calc.py", code)
    assert len(findings) == 0


def test_ast_analyzer_syntax_error():
    code = "def broken(\n    return 42\n"
    findings = PythonASTAnalyzer.analyze("broken.py", code)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "AST-SYNTAX-ERROR"
    assert f.severity == FindingSeverity.CRITICAL
    assert f.category == FindingCategory.CORRECTNESS
    assert f.source == FindingSource.STATIC_ANALYSIS
    assert f.line_start == 2 or f.line_start == 1


def test_ast_analyzer_detects_eval():
    code = "user_input = '__import__(\"os\").system(\"ls\")'\nresult = eval(user_input)\n"
    findings = PythonASTAnalyzer.analyze("unsafe.py", code)

    assert any(f.rule_id == "AST-EVAL" and f.severity == FindingSeverity.HIGH for f in findings)


def test_ast_analyzer_detects_exec():
    code = "code_str = 'x = 10'\nexec(code_str)\n"
    findings = PythonASTAnalyzer.analyze("dynamic.py", code)

    assert any(f.rule_id == "AST-EXEC" and f.severity == FindingSeverity.HIGH for f in findings)


def test_ast_analyzer_detects_os_system():
    code = "import os\ncmd = 'rm -rf /'\nos.system(cmd)\n"
    findings = PythonASTAnalyzer.analyze("command.py", code)

    assert any(f.rule_id == "AST-OS-SYSTEM" and f.severity == FindingSeverity.HIGH for f in findings)


def test_ast_analyzer_detects_subprocess_shell():
    code = "import subprocess\nsubprocess.run('echo hello', shell=True)\n"
    findings = PythonASTAnalyzer.analyze("proc.py", code)

    assert any(f.rule_id == "AST-SUBPROCESS-SHELL" and f.severity == FindingSeverity.HIGH for f in findings)


def test_ast_analyzer_detects_empty_except():
    code = (
        "try:\n"
        "    x = 1 / 0\n"
        "except Exception:\n"
        "    pass\n"
    )
    findings = PythonASTAnalyzer.analyze("handler.py", code)

    assert any(f.rule_id == "AST-EMPTY-EXCEPT" and f.category == FindingCategory.ERROR_HANDLING for f in findings)


def test_ast_analyzer_detects_excessive_nesting():
    code = (
        "def deeply_nested(x):\n"
        "    if x > 0:\n"
        "        for i in range(x):\n"
        "            while i < 10:\n"
        "                if i % 2 == 0:\n"
        "                    for k in range(3):\n"
        "                        print(k)\n"
    )
    findings = PythonASTAnalyzer.analyze("nested.py", code)

    assert any(f.rule_id == "AST-EXCESSIVE-NESTING" and f.category == FindingCategory.MAINTAINABILITY for f in findings)


def test_ast_analyzer_detects_missing_docstring():
    # File with >= 10 non-empty lines without docstring
    code = "\n".join([f"var_{i} = {i}" for i in range(12)])
    findings = PythonASTAnalyzer.analyze("nodoc.py", code)

    assert any(f.rule_id == "AST-MISSING-DOCSTRING" and f.severity == FindingSeverity.INFO for f in findings)
