"""Unit tests for Phase 14 JavaLanguageAdapter."""

import pytest
from app.code_intelligence.adapters.java_adapter import JavaLanguageAdapter
from app.code_intelligence.contracts import (
    AuthorityClassification,
    CodeLanguage,
    SymbolKind,
)


def test_java_adapter_package_symbols_and_inheritance():
    """Verify package, classes, interfaces, inheritance, and constructors."""
    code = """
package com.example.platform.service;

import java.util.List;
import java.util.UUID;
import com.example.platform.model.User;
import com.example.platform.repository.UserRepository;

public class UserServiceImpl extends BaseService implements IUserService {
    private final UserRepository repository;

    public UserServiceImpl(UserRepository repository) {
        this.repository = repository;
    }

    public User findById(UUID id) {
        return repository.findById(id);
    }
}
"""
    adapter = JavaLanguageAdapter()
    cf = adapter.safe_parse("src/main/java/com/example/platform/service/UserServiceImpl.java", code)

    assert cf.language == CodeLanguage.JAVA
    assert cf.has_syntax_error is False

    sym_map = {s.name: s for s in cf.symbols}
    assert "com.example.platform.service" in sym_map
    assert sym_map["com.example.platform.service"].kind == SymbolKind.PACKAGE

    assert "UserServiceImpl" in sym_map
    assert sym_map["UserServiceImpl"].kind == SymbolKind.CLASS
    assert sym_map["UserServiceImpl"].is_exported is True

    assert "BaseService" in sym_map
    assert sym_map["BaseService"].signature == "extends"

    assert "IUserService" in sym_map
    assert sym_map["IUserService"].signature == "implements"

    assert "UserServiceImpl" in sym_map
    assert "findById" in sym_map
    assert sym_map["findById"].kind == SymbolKind.METHOD


def test_java_adapter_reflection_detection():
    """Verify reflection calls are flagged as uncertainties."""
    code = """
package com.example.dynamic;

public class PluginLoader {
    public Object load(String className) throws Exception {
        Class<?> clazz = Class.forName(className);
        return clazz.getDeclaredMethod("create").invoke(null);
    }
}
"""
    adapter = JavaLanguageAdapter()
    cf = adapter.safe_parse("src/com/example/dynamic/PluginLoader.java", code)

    assert cf.has_dynamic_constructs is True
    assert any(d.error_type == "REFLECTION_DETECTED" for d in cf.diagnostics)


def test_java_adapter_internal_dependency_resolution():
    """Verify resolution of package and class imports to project files."""
    adapter = JavaLanguageAdapter()
    code = """
package com.example.service;

import com.example.model.User;
import com.example.util.*;
import org.springframework.stereotype.Service;
"""
    cf = adapter.safe_parse("src/com/example/service/OrderService.java", code)
    all_files = [
        "src/com/example/service/OrderService.java",
        "src/com/example/model/User.java",
        "src/com/example/util/DateUtil.java",
        "src/com/example/util/StringUtil.java",
        "pom.xml",
    ]

    edges = adapter.resolve_internal_dependencies("src/com/example/service/OrderService.java", cf.imports, all_files)

    resolved = {e.target_file: e for e in edges if e.is_resolved}
    assert "src/com/example/model/User.java" in resolved
    assert "src/com/example/util/DateUtil.java" in resolved
    assert "src/com/example/util/StringUtil.java" in resolved

    # org.springframework is external -> unresolved
    unresolved = [e for e in edges if not e.is_resolved]
    assert any("springframework" in e.target_file for e in unresolved)


def test_java_generics_nested_and_string_comment_isolation():
    """Verify Java generic parameters (<User, UUID>), strings, comments, and reflection isolation."""
    adapter = JavaLanguageAdapter()
    code = """
package com.example.service;

String fake = "class Fake {}";
String fake2 = "interface FakeInterface {}";
// class CommentedClass {}
/* class AnotherFake {} */
String text = "implements FakeInterface";
// Class.forName("com.example.Fake");
String ref = "Class.forName(\\"bad.Class\\")";

public class UserService implements IUserService<User, UUID> {
    public UserService() {}
}

public class Child extends Base<Thing> implements IService<Map<String, List<User>>> {
    public Child() {}
}
"""
    cf = adapter.safe_parse("src/UserService.java", code)

    # 1. No false reflection diagnostic from comments or strings
    assert len(cf.diagnostics) == 0
    assert cf.has_dynamic_constructs is False

    # 2. Real symbols
    sym_map = {s.name: s for s in cf.symbols}
    assert "UserService" in sym_map
    assert "IUserService" in sym_map
    assert sym_map["IUserService"].signature == "implements"

    assert "Child" in sym_map
    assert "Base" in sym_map
    assert sym_map["Base"].signature == "extends"

    assert "IService" in sym_map
    assert sym_map["IService"].signature == "implements"

    # 3. No generic parameters leaked or corrupted as symbols
    assert "UUID>" not in sym_map
    assert "Thing>" not in sym_map
    assert "User>" not in sym_map
    assert "User" not in sym_map
    assert "UUID" not in sym_map

    # 4. No fake classes from strings or comments
    assert "Fake" not in sym_map
    assert "FakeInterface" not in sym_map
    assert "CommentedClass" not in sym_map
    assert "AnotherFake" not in sym_map

