"""Unit tests for Phase 14 TypeScriptLanguageAdapter."""

import pytest
from app.code_intelligence.adapters.typescript_adapter import TypeScriptLanguageAdapter
from app.code_intelligence.contracts import (
    AuthorityClassification,
    CodeLanguage,
    SymbolKind,
)


def test_typescript_adapter_types_and_interfaces():
    """Verify TypeScript interfaces, types, enums, and classes."""
    code = """
import type { UserRole, Permissions } from './types';
import { BaseService } from './baseService';

export interface UserProfile {
    id: string;
    username: string;
    role: UserRole;
}

export type Result<T> = { data: T } | { error: string };

export enum Status {
    ACTIVE = "ACTIVE",
    SUSPENDED = "SUSPENDED"
}

export class UserService extends BaseService {
    public async fetchUser(id: string): Promise<UserProfile> {
        return { id, username: "dev", role: "admin" as UserRole };
    }
}
"""
    adapter = TypeScriptLanguageAdapter()
    cf = adapter.safe_parse("src/services/userService.ts", code)

    assert cf.language == CodeLanguage.TYPESCRIPT
    assert cf.has_syntax_error is False

    sym_map = {s.name: s for s in cf.symbols}
    assert "UserProfile" in sym_map
    assert sym_map["UserProfile"].kind == SymbolKind.INTERFACE
    assert sym_map["UserProfile"].is_exported is True

    assert "Result" in sym_map
    assert sym_map["Result"].kind == SymbolKind.TYPE_ALIAS

    assert "Status" in sym_map
    assert sym_map["Status"].kind == SymbolKind.ENUM

    assert "UserService" in sym_map
    assert sym_map["UserService"].kind == SymbolKind.CLASS

    assert "fetchUser" in sym_map
    assert sym_map["fetchUser"].kind == SymbolKind.METHOD

    # Check type imports
    type_imports = [i for i in cf.imports if i.module == "./types"]
    assert len(type_imports) > 0
    assert "UserRole" in type_imports[0].imported_symbols
    assert "Permissions" in type_imports[0].imported_symbols


def test_typescript_cross_language_resolution():
    """Verify TypeScript imports resolving to both .ts and .js/.jsx files."""
    adapter = TypeScriptLanguageAdapter()
    code = """
import { helper } from '../utils/legacyHelper';
import { Button } from '../components/Button';
import { AppState } from './types';
"""
    cf = adapter.safe_parse("src/views/Dashboard.tsx", code)
    all_files = [
        "src/views/Dashboard.tsx",
        "src/utils/legacyHelper.js",       # JS target!
        "src/components/Button.tsx",       # TSX target!
        "src/views/types.ts",             # TS target!
    ]

    edges = adapter.resolve_internal_dependencies("src/views/Dashboard.tsx", cf.imports, all_files)

    resolved = {e.target_file: e for e in edges if e.is_resolved}
    assert "src/utils/legacyHelper.js" in resolved
    assert resolved["src/utils/legacyHelper.js"].authority == AuthorityClassification.DETERMINISTIC

    assert "src/components/Button.tsx" in resolved
    assert "src/views/types.ts" in resolved


def test_typescript_generic_classes_functions_and_isolation():
    """Verify TypeScript generic classes, functions, nested generics, and comments."""
    adapter = TypeScriptLanguageAdapter()
    code = """
// import fake from './fake1';
const fakeStr = "import fake from './fake2'";

export class UserService<T extends BaseEntity> implements IService<T> {
    public constructor() {}
}

export function findById<T>(id: string): T {
    return null;
}

export interface Repository<T extends Record<string, any>> {
    get(id: string): T;
}

export type Store<T> = Map<string, T>;
"""
    cf = adapter.safe_parse("src/generics.ts", code)

    # 1. Imports: zero false imports from comments/strings
    assert len(cf.imports) == 0

    # 2. Symbols
    sym_map = {s.name: s for s in cf.symbols}
    assert "UserService" in sym_map
    assert sym_map["UserService"].kind == SymbolKind.CLASS

    assert "IService" in sym_map
    assert sym_map["IService"].kind == SymbolKind.INTERFACE

    assert "findById" in sym_map
    assert sym_map["findById"].kind == SymbolKind.FUNCTION

    assert "Repository" in sym_map
    assert sym_map["Repository"].kind == SymbolKind.INTERFACE

    assert "Store" in sym_map
    assert sym_map["Store"].kind == SymbolKind.TYPE_ALIAS

    # Ensure generic type parameters did not leak as separate declarations
    assert "T" not in sym_map
    assert "BaseEntity" not in sym_map

