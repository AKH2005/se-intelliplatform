"""Unit tests for Phase 14 Polyglot Language and Technology Detector."""

import pytest
from app.code_intelligence.contracts import (
    CodeLanguage,
    DatabaseParadigm,
    TechnologyCategory,
)
from app.code_intelligence.detector import (
    LanguageDetector,
    TechnologyDetector,
    mask_credentials,
)


def test_language_detection_by_extension():
    """Verify deterministic language mapping for all 13 core languages and web technologies."""
    # Python
    assert LanguageDetector.detect("backend/main.py") == CodeLanguage.PYTHON
    assert LanguageDetector.detect("app/types.pyi") == CodeLanguage.PYTHON
    assert LanguageDetector.detect("module.pyx") == CodeLanguage.PYTHON

    # JavaScript
    assert LanguageDetector.detect("frontend/index.js") == CodeLanguage.JAVASCRIPT
    assert LanguageDetector.detect("components/App.jsx") == CodeLanguage.JAVASCRIPT
    assert LanguageDetector.detect("server.mjs") == CodeLanguage.JAVASCRIPT
    assert LanguageDetector.detect("bundle.cjs") == CodeLanguage.JAVASCRIPT

    # TypeScript
    assert LanguageDetector.detect("src/index.ts") == CodeLanguage.TYPESCRIPT
    assert LanguageDetector.detect("src/views/Home.tsx") == CodeLanguage.TYPESCRIPT
    assert LanguageDetector.detect("utils.mts") == CodeLanguage.TYPESCRIPT
    assert LanguageDetector.detect("config.cts") == CodeLanguage.TYPESCRIPT

    # Java
    assert LanguageDetector.detect("src/main/java/UserService.java") == CodeLanguage.JAVA

    # C / C++
    assert LanguageDetector.detect("src/main.c") == CodeLanguage.C
    assert LanguageDetector.detect("include/header.h") == CodeLanguage.C
    assert LanguageDetector.detect("src/core.cpp") == CodeLanguage.CPP
    assert LanguageDetector.detect("src/engine.cc") == CodeLanguage.CPP
    assert LanguageDetector.detect("include/core.hpp") == CodeLanguage.CPP

    # C#
    assert LanguageDetector.detect("src/Program.cs") == CodeLanguage.CSHARP

    # Go
    assert LanguageDetector.detect("cmd/main.go") == CodeLanguage.GO

    # Rust
    assert LanguageDetector.detect("src/lib.rs") == CodeLanguage.RUST

    # PHP
    assert LanguageDetector.detect("index.php") == CodeLanguage.PHP

    # Ruby
    assert LanguageDetector.detect("app.rb") == CodeLanguage.RUBY
    assert LanguageDetector.detect("Rakefile.rake") == CodeLanguage.RUBY

    # Kotlin
    assert LanguageDetector.detect("App.kt") == CodeLanguage.KOTLIN
    assert LanguageDetector.detect("build.gradle.kts") == CodeLanguage.KOTLIN

    # Swift
    assert LanguageDetector.detect("AppDelegate.swift") == CodeLanguage.SWIFT

    # Web Technologies
    assert LanguageDetector.detect("public/index.html") == CodeLanguage.HTML
    assert LanguageDetector.detect("styles/app.css") == CodeLanguage.CSS
    assert LanguageDetector.detect("styles/theme.scss") == CodeLanguage.CSS
    assert LanguageDetector.detect("db/schema.sql") == CodeLanguage.SQL
    assert LanguageDetector.detect("package.json") == CodeLanguage.JSON
    assert LanguageDetector.detect("config.yaml") == CodeLanguage.YAML
    assert LanguageDetector.detect("ci.yml") == CodeLanguage.YAML

    # Unknown
    assert LanguageDetector.detect("readme.md") == CodeLanguage.UNKNOWN
    assert LanguageDetector.detect("binary.xyz") == CodeLanguage.UNKNOWN


def test_language_detection_by_shebang():
    """Verify shebang detection for extensionless script files."""
    py_script = "#!/usr/bin/env python3\nprint('hello')\n"
    assert LanguageDetector.detect("bin/my-script", py_script) == CodeLanguage.PYTHON

    node_script = "#!/usr/bin/env node\nconsole.log('hello');\n"
    assert LanguageDetector.detect("bin/runner", node_script) == CodeLanguage.JAVASCRIPT

    ruby_script = "#!/usr/bin/env ruby\nputs 'hello'\n"
    assert LanguageDetector.detect("bin/ruby-task", ruby_script) == CodeLanguage.RUBY


def test_test_file_detection():
    """Verify test file pattern classification across languages."""
    assert LanguageDetector.is_test_file("tests/unit/test_models.py") is True
    assert LanguageDetector.is_test_file("app/models.py") is False
    assert LanguageDetector.is_test_file("src/test/button.test.tsx") is True
    assert LanguageDetector.is_test_file("src/specs/auth.spec.ts") is True
    assert LanguageDetector.is_test_file("src/components/Button.tsx") is False
    assert LanguageDetector.is_test_file("src/test/java/UserServiceTest.java") is True
    assert LanguageDetector.is_test_file("src/main/java/UserService.java") is False


def test_credential_masking():
    """Verify passwords in connection strings and configs are masked with ***."""
    uri = "mysql://admin:SuperSecret123@localhost:3306/production_db"
    masked = mask_credentials(uri)
    assert "SuperSecret123" not in masked
    assert "mysql://admin:***@localhost:3306/production_db" in masked

    pg_uri = "postgresql://user:db_pass_xyz@db.host.com:5432/app"
    masked_pg = mask_credentials(pg_uri)
    assert "db_pass_xyz" not in masked_pg
    assert "postgresql://user:***@db.host.com:5432/app" in masked_pg

    mongo_uri = "mongodb+srv://root:MySecretMongoPass@cluster0.mongodb.net/test"
    masked_mongo = mask_credentials(mongo_uri)
    assert "MySecretMongoPass" not in masked_mongo
    assert "mongodb+srv://root:***@cluster0.mongodb.net/test" in masked_mongo


def test_technology_detection_polyglot_and_frameworks():
    """Verify detection of programming languages and frameworks from repository manifests."""
    files = {
        "requirements.txt": "fastapi>=0.100.0\nuvicorn\nsqlalchemy\n",
        "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "package.json": '{"dependencies": {"react": "^18.2.0", "typescript": "^5.0.0"}}',
        "src/App.tsx": "export const App = () => <div>Hello</div>;",
        "go.mod": "module myapp\ngo 1.21\nrequire github.com/gin-gonic/gin v1.9.1\n",
        "main.go": "package main\nimport \"github.com/gin-gonic/gin\"\nfunc main() {}\n",
    }
    techs = TechnologyDetector.detect_project_technologies(files)
    tech_names = {t.name for t in techs}

    assert "Python" in tech_names
    assert "TypeScript" in tech_names
    assert "Go" in tech_names

    py_tech = next(t for t in techs if t.name == "Python")
    assert py_tech.category == TechnologyCategory.PROGRAMMING_LANGUAGE
    assert "FastAPI" in py_tech.detected_frameworks
    assert py_tech.capabilities.can_ast_analyze is True

    go_tech = next(t for t in techs if t.name == "Go")
    assert go_tech.category == TechnologyCategory.PROGRAMMING_LANGUAGE
    assert "Gin" in go_tech.detected_frameworks


def test_database_technology_detection_relational_vs_document():
    """Verify distinct detection of MySQL, PostgreSQL, SQLite, and MongoDB with proper paradigms."""
    repo_files = {
        # MySQL indicators
        "backend/.env": "MYSQL_URL=mysql://dbuser:mypassword@db.internal:3306/se_platform\nMYSQL_DATABASE=se_platform",
        "backend/db/init.sql": "CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB;",
        # MongoDB indicators
        "frontend/src/models/user.ts": "import mongoose, { Schema } from 'mongoose';\nconst schema = new Schema({ name: String });\nexport default mongoose.model('User', schema);",
        "backend/analytics.py": "from pymongo import MongoClient\nclient = MongoClient('mongodb://admin:secret999@localhost:27017/')\npipeline = [{'$match': {'status': 'active'}}, {'$group': {'_id': '$role'}}]",
        # PostgreSQL indicators
        "backend/requirements.txt": "psycopg2-binary>=2.9.0\nasyncpg>=0.28.0\n",
        # SQLite indicators
        "backend/dev.db": "dummy_binary_sqlite",
    }

    techs = TechnologyDetector.detect_project_technologies(repo_files)
    tech_map = {t.name: t for t in techs}

    assert "MySQL" in tech_map
    mysql = tech_map["MySQL"]
    assert mysql.category == TechnologyCategory.DATABASE_ENGINE
    assert mysql.paradigm == DatabaseParadigm.RELATIONAL
    assert any("mypassword" not in ev and "***" in ev for ev in mysql.evidence)

    assert "MongoDB" in tech_map
    mongo = tech_map["MongoDB"]
    assert mongo.category == TechnologyCategory.DATABASE_ENGINE
    assert mongo.paradigm == DatabaseParadigm.DOCUMENT
    assert any("secret999" not in ev and "***" in ev for ev in mongo.evidence)
    assert any("aggregation" in ev.lower() or "mongoose" in ev.lower() for ev in mongo.evidence)

    assert "PostgreSQL" in tech_map
    pg = tech_map["PostgreSQL"]
    assert pg.category == TechnologyCategory.DATABASE_ENGINE
    assert pg.paradigm == DatabaseParadigm.RELATIONAL
    assert any("psycopg2" in d.lower() or "asyncpg" in d.lower() for d in pg.detected_drivers)

    assert "SQLite" in tech_map
    sqlite = tech_map["SQLite"]
    assert sqlite.category == TechnologyCategory.DATABASE_ENGINE
    assert sqlite.paradigm == DatabaseParadigm.RELATIONAL
