"""Unit tests for Phase 14 JavaScriptLanguageAdapter."""

import pytest
from app.code_intelligence.adapters.javascript_adapter import JavaScriptLanguageAdapter
from app.code_intelligence.contracts import (
    AuthorityClassification,
    CodeLanguage,
    SymbolKind,
)


def test_javascript_adapter_es_imports_and_exports():
    """Verify ES module imports and exports extraction."""
    code = """
import React, { useState, useEffect as useAsyncEffect } from 'react';
import Header from './components/Header';
import { calculateSum } from '../utils/math';

export const API_URL = "https://api.example.com";

export default function App() {
    return <div>Hello</div>;
}

export { calculateSum as addNumbers };
"""
    adapter = JavaScriptLanguageAdapter()
    cf = adapter.safe_parse("src/App.jsx", code)

    assert cf.language == CodeLanguage.JAVASCRIPT
    assert cf.has_syntax_error is False

    modules = {i.module: i for i in cf.imports}
    assert "react" in modules
    assert "React" in modules["react"].imported_symbols
    assert "useState" in modules["react"].imported_symbols
    assert "useEffect" in modules["react"].imported_symbols

    assert "./components/Header" in modules
    assert modules["./components/Header"].is_relative is True

    assert "../utils/math" in modules
    assert modules["../utils/math"].is_relative is True

    export_names = {e.name for e in cf.exports}
    assert "API_URL" in export_names
    assert "App" in export_names
    assert "addNumbers" in export_names


def test_javascript_commonjs_require_and_exports():
    """Verify CommonJS require() and module.exports extraction."""
    code = """
const path = require('path');
const { readFileSync, writeFileSync } = require('fs');
const logger = require('./logger');

class FileService {
    constructor(baseDir) {
        this.baseDir = baseDir;
    }

    read(fileName) {
        return readFileSync(path.join(this.baseDir, fileName));
    }
}

module.exports = FileService;
exports.helper = function() {};
"""
    adapter = JavaScriptLanguageAdapter()
    cf = adapter.safe_parse("server/fileService.js", code)

    assert cf.language == CodeLanguage.JAVASCRIPT

    modules = {i.module: i for i in cf.imports}
    assert "path" in modules
    assert "fs" in modules
    assert "readFileSync" in modules["fs"].imported_symbols
    assert "./logger" in modules

    sym_names = {s.name: s for s in cf.symbols}
    assert "FileService" in sym_names
    assert sym_names["FileService"].kind == SymbolKind.CLASS

    assert "constructor" in sym_names
    assert sym_names["constructor"].kind == SymbolKind.CONSTRUCTOR

    assert "read" in sym_names
    assert sym_names["read"].kind == SymbolKind.METHOD

    exports = {e.name for e in cf.exports}
    assert "default" in exports or "FileService" in exports
    assert "helper" in exports


def test_javascript_dynamic_and_eval_detection():
    """Verify dynamic imports and eval() are flagged as uncertainties."""
    code = """
const modName = 'plugin-' + id;
const dynamicPlugin = require(modName);

async function loadRoute(route) {
    const chunk = await import(`./routes/${route}`);
    eval("console.log('danger')");
    return chunk;
}
"""
    adapter = JavaScriptLanguageAdapter()
    cf = adapter.safe_parse("src/dynamic.js", code)

    assert cf.has_dynamic_constructs is True
    err_types = {d.error_type for d in cf.diagnostics}
    assert "DYNAMIC_REQUIRE" in err_types
    assert "DYNAMIC_IMPORT" in err_types
    assert "DYNAMIC_CODE_EXECUTION" in err_types


def test_javascript_relative_dependency_resolution():
    """Verify resolution of relative module paths across project files."""
    adapter = JavaScriptLanguageAdapter()
    code = """
import Header from './Header';
import { Footer } from './Footer.jsx';
import { api } from '../services/api';
import _ from 'lodash';
"""
    cf = adapter.safe_parse("src/components/Layout.js", code)
    all_files = [
        "src/components/Layout.js",
        "src/components/Header.js",
        "src/components/Footer.jsx",
        "src/services/api/index.js",
        "package.json",
    ]

    edges = adapter.resolve_internal_dependencies("src/components/Layout.js", cf.imports, all_files)

    resolved = {e.target_file: e for e in edges if e.is_resolved}
    assert "src/components/Header.js" in resolved
    assert "src/components/Footer.jsx" in resolved
    assert "src/services/api/index.js" in resolved

    # lodash is external -> marked unresolved
    unresolved = [e for e in edges if not e.is_resolved]
    assert any(e.target_file == "lodash" for e in unresolved)


def test_javascript_lexical_comment_and_string_isolation():
    """Verify comments, strings, and template literals containing syntax do not create imports."""
    adapter = JavaScriptLanguageAdapter()
    code = """
// import fake1 from './fake1';
/*
  const fake2 = require('./fake2');
*/
const str1 = "import fake3 from './fake3'";
const str2 = '// require("./fake4")';
const tmpl1 = `import fake5 from "./fake5"`;
const tmpl2 = `
{
   require('./fake6');
}
`;

// Real imports
import { real1 } from './real1';
const real2 = require('./real2');
"""
    cf = adapter.safe_parse("src/isolation.js", code)

    imported_modules = [i.module for i in cf.imports]
    assert imported_modules == ["./real1", "./real2"], f"Unexpected imports: {imported_modules}"

    all_files = [
        "src/isolation.js",
        "src/fake1.js",
        "src/fake2.js",
        "src/fake3.js",
        "src/fake4.js",
        "src/fake5.js",
        "src/fake6.js",
        "src/real1.js",
        "src/real2.js",
    ]
    edges = adapter.resolve_internal_dependencies("src/isolation.js", cf.imports, all_files)
    target_files = [e.target_file for e in edges]
    assert target_files == ["src/real1.js", "src/real2.js"]

