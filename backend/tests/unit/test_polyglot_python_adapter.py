"""Unit tests for Phase 14 PythonLanguageAdapter."""

import pytest
from app.code_intelligence.adapters.python_adapter import PythonLanguageAdapter
from app.code_intelligence.contracts import (
    AuthorityClassification,
    CodeLanguage,
    DependencyRelation,
    SymbolKind,
)


def test_python_adapter_symbol_extraction():
    """Verify classes, methods, functions, and docstrings extraction."""
    code = '''"""Module docstring."""

def standalone_func(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

class Calculator:
    """Calculator class."""
    def __init__(self, initial: int = 0):
        self.val = initial

    def add(self, x: int) -> int:
        return self.val + x
'''
    adapter = PythonLanguageAdapter()
    cf = adapter.safe_parse("app/calc.py", code)

    assert cf.language == CodeLanguage.PYTHON
    assert cf.has_syntax_error is False
    assert len(cf.symbols) >= 4

    names = {s.name: s for s in cf.symbols}
    assert "standalone_func" in names
    assert names["standalone_func"].kind == SymbolKind.FUNCTION
    assert names["standalone_func"].docstring == "Add two numbers."

    assert "Calculator" in names
    assert names["Calculator"].kind == SymbolKind.CLASS

    assert "__init__" in names
    assert names["__init__"].kind == SymbolKind.CONSTRUCTOR
    assert names["__init__"].parent_symbol == "Calculator"

    assert "add" in names
    assert names["add"].kind == SymbolKind.METHOD
    assert names["add"].parent_symbol == "Calculator"


def test_python_adapter_imports_and_dynamic_calls():
    """Verify static imports, dynamic __import__, and importlib detection."""
    code = """
import os
import sys
from app.models.user import User, Role
from .utils import helper

def dynamic_loader(pkg):
    mod = __import__(pkg)
    mod2 = importlib.import_module("dynamic_pkg")
    eval("1 + 1")
    return mod
"""
    adapter = PythonLanguageAdapter()
    cf = adapter.safe_parse("app/services/auth.py", code)

    assert cf.has_dynamic_constructs is True
    assert any(d.error_type == "DYNAMIC_IMPORT" for d in cf.diagnostics)

    import_modules = [i.module for i in cf.imports]
    assert "os" in import_modules
    assert "app.models.user" in import_modules
    assert ".utils" in import_modules
    assert "<dynamic>" in import_modules


def test_python_adapter_internal_dependency_resolution():
    """Verify internal relative and absolute module dependency resolution."""
    adapter = PythonLanguageAdapter()
    code = """
from app.models.user import User
from .helpers import validate_email
import requests
"""
    cf = adapter.safe_parse("app/services/auth.py", code)
    all_files = [
        "app/services/auth.py",
        "app/services/helpers.py",
        "app/models/user.py",
        "app/main.py",
    ]

    edges = adapter.resolve_internal_dependencies("app/services/auth.py", cf.imports, all_files)

    resolved = {e.target_file: e for e in edges if e.is_resolved}
    assert "app/models/user.py" in resolved
    assert resolved["app/models/user.py"].authority == AuthorityClassification.DETERMINISTIC
    assert resolved["app/models/user.py"].symbol == "User"

    assert "app/services/helpers.py" in resolved
    assert resolved["app/services/helpers.py"].authority == AuthorityClassification.DETERMINISTIC

    # requests is external -> marked unresolved
    unresolved = [e for e in edges if not e.is_resolved]
    assert any(e.target_file == "requests" for e in unresolved)


def test_python_syntax_error_isolation():
    """Verify malformed Python does not crash adapter and produces structured diagnostic."""
    bad_code = "def broken_syntax(:\n    pass\n"
    adapter = PythonLanguageAdapter()
    cf = adapter.safe_parse("broken.py", bad_code)

    assert cf.has_syntax_error is True
    assert len(cf.diagnostics) > 0
    assert cf.diagnostics[0].error_type == "SYNTAX_ERROR"
    assert cf.language == CodeLanguage.PYTHON
