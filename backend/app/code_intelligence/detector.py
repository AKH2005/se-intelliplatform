"""Deterministic Language and Technology Detector for Polyglot Code Intelligence.

Identifies source code languages, web technologies, and database technologies
based on file extensions, path patterns, manifests, and content evidence.
Zero LLMs. Safe fallback to CodeLanguage.UNKNOWN for unsupported files.
"""

import json
import os
import re
from typing import Any

from app.code_intelligence.contracts import (
    CodeLanguage,
    DatabaseParadigm,
    TechnologyCapability,
    TechnologyCategory,
    TechnologyDetection,
    get_honest_capabilities,
    get_technology_category,
)

# Deterministic extension-to-language map
EXTENSION_LANGUAGE_MAP: dict[str, CodeLanguage] = {
    # Python
    ".py": CodeLanguage.PYTHON,
    ".pyi": CodeLanguage.PYTHON,
    ".pyx": CodeLanguage.PYTHON,

    # JavaScript
    ".js": CodeLanguage.JAVASCRIPT,
    ".jsx": CodeLanguage.JAVASCRIPT,
    ".mjs": CodeLanguage.JAVASCRIPT,
    ".cjs": CodeLanguage.JAVASCRIPT,

    # TypeScript
    ".ts": CodeLanguage.TYPESCRIPT,
    ".tsx": CodeLanguage.TYPESCRIPT,
    ".mts": CodeLanguage.TYPESCRIPT,
    ".cts": CodeLanguage.TYPESCRIPT,

    # Java
    ".java": CodeLanguage.JAVA,

    # C
    ".c": CodeLanguage.C,
    ".h": CodeLanguage.C,

    # C++
    ".cpp": CodeLanguage.CPP,
    ".hpp": CodeLanguage.CPP,
    ".cc": CodeLanguage.CPP,
    ".cxx": CodeLanguage.CPP,
    ".hxx": CodeLanguage.CPP,

    # C#
    ".cs": CodeLanguage.CSHARP,

    # Go
    ".go": CodeLanguage.GO,

    # Rust
    ".rs": CodeLanguage.RUST,

    # PHP
    ".php": CodeLanguage.PHP,
    ".phtml": CodeLanguage.PHP,

    # Ruby
    ".rb": CodeLanguage.RUBY,
    ".rake": CodeLanguage.RUBY,

    # Kotlin
    ".kt": CodeLanguage.KOTLIN,
    ".kts": CodeLanguage.KOTLIN,

    # Swift
    ".swift": CodeLanguage.SWIFT,

    # Web Technologies & Dialects
    ".html": CodeLanguage.HTML,
    ".htm": CodeLanguage.HTML,
    ".css": CodeLanguage.CSS,
    ".scss": CodeLanguage.CSS,
    ".sass": CodeLanguage.CSS,
    ".less": CodeLanguage.CSS,
    ".sql": CodeLanguage.SQL,
    ".json": CodeLanguage.JSON,
    ".yaml": CodeLanguage.YAML,
    ".yml": CodeLanguage.YAML,
}

# Known test file patterns across languages
TEST_FILE_PATTERNS: tuple[str, ...] = (
    "test_",
    "_test.",
    ".test.",
    ".spec.",
    "Test.",
    "Tests.",
    "/tests/",
    "/test/",
    "/__tests__/",
)

# URI masking pattern to hide sensitive credentials
URI_PASSWORD_PATTERN = re.compile(r"://([^:@\s]+):([^@\s]+)@")


def mask_credentials(text: str) -> str:
    """Mask passwords in connection strings and sensitive configurations."""
    masked = URI_PASSWORD_PATTERN.sub(r"://\1:***@", text)
    # Mask key-value credentials like password=xyz or PWD=xyz
    masked = re.sub(r"(password|pwd|secret|auth)=([^\s;&]+)", r"\1=***", masked, flags=re.IGNORECASE)
    return masked


class LanguageDetector:
    """Pure deterministic language detector."""

    @classmethod
    def detect(cls, file_path: str, content: str | None = None) -> CodeLanguage:
        """Detect language from file path extension or shebang.
        
        Args:
            file_path: Relative or absolute file path.
            content: Optional file content string for shebang inspection.
            
        Returns:
            CodeLanguage: Detected language, or CodeLanguage.UNKNOWN if unsupported.
        """
        clean_path = str(file_path).replace("\\", "/").strip().lower()
        _, ext = os.path.splitext(clean_path)

        if ext in EXTENSION_LANGUAGE_MAP:
            return EXTENSION_LANGUAGE_MAP[ext]

        # Shebang inspection for extensionless script files
        if content and content.startswith("#!"):
            first_line = content.splitlines()[0].lower()
            if "python" in first_line:
                return CodeLanguage.PYTHON
            if "node" in first_line or "deno" in first_line or "bun" in first_line:
                return CodeLanguage.JAVASCRIPT
            if "ruby" in first_line:
                return CodeLanguage.RUBY
            if "php" in first_line:
                return CodeLanguage.PHP

        return CodeLanguage.UNKNOWN

    @classmethod
    def is_test_file(cls, file_path: str) -> bool:
        """Deterministically determine if a file represents a unit, integration, or spec test."""
        clean_path = str(file_path).replace("\\", "/").strip().lower()
        base_name = os.path.basename(clean_path)

        for pat in TEST_FILE_PATTERNS:
            if pat in clean_path or pat in base_name:
                return True

        return False


class TechnologyDetector:
    """Detects programming languages, frameworks, and database technologies from repository files."""

    @classmethod
    def detect_project_technologies(cls, files_map: dict[str, str]) -> list[TechnologyDetection]:
        """Inspect all project files to deterministically identify languages, frameworks, and databases."""
        results: list[TechnologyDetection] = []
        file_counts_by_lang: dict[CodeLanguage, int] = {}
        files_by_lang: dict[CodeLanguage, list[str]] = {}

        # 1. Count and group files by language
        for path, content in files_map.items():
            lang = LanguageDetector.detect(path, content)
            if lang != CodeLanguage.UNKNOWN:
                file_counts_by_lang[lang] = file_counts_by_lang.get(lang, 0) + 1
                files_by_lang.setdefault(lang, []).append(path)

        # 2. Inspect manifests and files for programming languages & frameworks
        manifest_evidence: dict[str, list[str]] = {}
        detected_frameworks: dict[str, list[str]] = {}

        # Check Python manifests
        python_files = files_by_lang.get(CodeLanguage.PYTHON, [])
        py_reqs = files_map.get("requirements.txt") or files_map.get("backend/requirements.txt") or ""
        py_project = files_map.get("pyproject.toml") or files_map.get("backend/pyproject.toml") or ""
        py_evidence = []
        py_frameworks = []
        if py_reqs or py_project:
            py_evidence.append("Found Python package manifest")
            combined_py = py_reqs.lower() + "\n" + py_project.lower()
            if "fastapi" in combined_py:
                py_frameworks.append("FastAPI")
            if "flask" in combined_py:
                py_frameworks.append("Flask")
            if "django" in combined_py:
                py_frameworks.append("Django")
            if "sqlalchemy" in combined_py:
                py_frameworks.append("SQLAlchemy")
        if python_files or py_evidence:
            confidence = 1.0 if python_files and py_evidence else (0.9 if python_files else 0.8)
            evidence = py_evidence + ([f"{len(python_files)} Python source file(s)"] if python_files else [])
            results.append(
                TechnologyDetection(
                    name="Python",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=confidence,
                    evidence=evidence,
                    file_paths=python_files[:10],
                    detected_frameworks=py_frameworks,
                    detected_drivers=[],
                    capabilities=get_honest_capabilities(CodeLanguage.PYTHON),
                )
            )

        # Check JS/TS manifests
        pkg_json_str = files_map.get("package.json") or files_map.get("frontend/package.json") or ""
        js_files = files_by_lang.get(CodeLanguage.JAVASCRIPT, [])
        ts_files = files_by_lang.get(CodeLanguage.TYPESCRIPT, [])
        js_frameworks = []
        has_ts_dep = False

        if pkg_json_str:
            try:
                pkg_data = json.loads(pkg_json_str)
                all_deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                if "typescript" in all_deps or any(k.startswith("@types/") for k in all_deps):
                    has_ts_dep = True
                if "react" in all_deps:
                    js_frameworks.append("React")
                if "next" in all_deps:
                    js_frameworks.append("Next.js")
                if "vue" in all_deps:
                    js_frameworks.append("Vue")
                if "express" in all_deps:
                    js_frameworks.append("Express")
                if "vite" in all_deps:
                    js_frameworks.append("Vite")
                if "@nestjs/core" in all_deps:
                    js_frameworks.append("NestJS")
            except Exception:
                pass

        if ts_files or has_ts_dep or "tsconfig.json" in files_map or "frontend/tsconfig.json" in files_map:
            results.append(
                TechnologyDetection(
                    name="TypeScript",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0 if ts_files else 0.85,
                    evidence=[f"{len(ts_files)} TypeScript file(s)"] if ts_files else ["Found tsconfig.json or typescript dependency"],
                    file_paths=ts_files[:10],
                    detected_frameworks=js_frameworks,
                    capabilities=get_honest_capabilities(CodeLanguage.TYPESCRIPT),
                )
            )

        if js_files or (pkg_json_str and not has_ts_dep):
            results.append(
                TechnologyDetection(
                    name="JavaScript",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0 if js_files else 0.8,
                    evidence=[f"{len(js_files)} JavaScript file(s)"] if js_files else ["Found package.json manifest"],
                    file_paths=js_files[:10],
                    detected_frameworks=js_frameworks,
                    capabilities=get_honest_capabilities(CodeLanguage.JAVASCRIPT),
                )
            )

        # Check Java manifests & files
        java_files = files_by_lang.get(CodeLanguage.JAVA, [])
        pom_xml = files_map.get("pom.xml") or files_map.get("backend/pom.xml") or ""
        gradle = files_map.get("build.gradle") or files_map.get("build.gradle.kts") or ""
        java_frameworks = []
        if "spring-boot" in pom_xml.lower() or "spring-boot" in gradle.lower():
            java_frameworks.append("Spring Boot")
        if "quarkus" in pom_xml.lower() or "quarkus" in gradle.lower():
            java_frameworks.append("Quarkus")
        if java_files or pom_xml or gradle:
            evidence = []
            if pom_xml:
                evidence.append("Found Maven pom.xml")
            if gradle:
                evidence.append("Found Gradle build file")
            if java_files:
                evidence.append(f"{len(java_files)} Java source file(s)")
            results.append(
                TechnologyDetection(
                    name="Java",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0 if java_files else 0.85,
                    evidence=evidence,
                    file_paths=java_files[:10],
                    detected_frameworks=java_frameworks,
                    capabilities=get_honest_capabilities(CodeLanguage.JAVA),
                )
            )

        # Check Go
        go_files = files_by_lang.get(CodeLanguage.GO, [])
        go_mod = files_map.get("go.mod") or ""
        go_frameworks = []
        if "gin-gonic/gin" in go_mod:
            go_frameworks.append("Gin")
        if "gofiber/fiber" in go_mod:
            go_frameworks.append("Fiber")
        if go_files or go_mod:
            results.append(
                TechnologyDetection(
                    name="Go",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0 if go_files else 0.85,
                    evidence=[f"{len(go_files)} Go source file(s)"] if go_files else ["Found go.mod manifest"],
                    file_paths=go_files[:10],
                    detected_frameworks=go_frameworks,
                    capabilities=get_honest_capabilities(CodeLanguage.GO),
                )
            )

        # Check Rust
        rust_files = files_by_lang.get(CodeLanguage.RUST, [])
        cargo_toml = files_map.get("Cargo.toml") or ""
        rust_frameworks = []
        if "actix-web" in cargo_toml:
            rust_frameworks.append("Actix Web")
        if "axum" in cargo_toml:
            rust_frameworks.append("Axum")
        if rust_files or cargo_toml:
            results.append(
                TechnologyDetection(
                    name="Rust",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0 if rust_files else 0.85,
                    evidence=[f"{len(rust_files)} Rust source file(s)"] if rust_files else ["Found Cargo.toml manifest"],
                    file_paths=rust_files[:10],
                    detected_frameworks=rust_frameworks,
                    capabilities=get_honest_capabilities(CodeLanguage.RUST),
                )
            )

        # Check C#
        cs_files = files_by_lang.get(CodeLanguage.CSHARP, [])
        csproj_files = [f for f in files_map if f.endswith(".csproj") or f.endswith(".sln")]
        if cs_files or csproj_files:
            results.append(
                TechnologyDetection(
                    name="C#",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0 if cs_files else 0.85,
                    evidence=[f"{len(cs_files)} C# file(s)"] if cs_files else [f"Found {len(csproj_files)} .csproj/.sln file(s)"],
                    file_paths=cs_files[:10],
                    capabilities=get_honest_capabilities(CodeLanguage.CSHARP),
                )
            )

        # Check C and C++
        c_files = files_by_lang.get(CodeLanguage.C, [])
        cpp_files = files_by_lang.get(CodeLanguage.CPP, [])
        if c_files:
            results.append(
                TechnologyDetection(
                    name="C",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0,
                    evidence=[f"{len(c_files)} C source/header file(s)"],
                    file_paths=c_files[:10],
                    capabilities=get_honest_capabilities(CodeLanguage.C),
                )
            )
        if cpp_files:
            results.append(
                TechnologyDetection(
                    name="C++",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0,
                    evidence=[f"{len(cpp_files)} C++ source/header file(s)"],
                    file_paths=cpp_files[:10],
                    capabilities=get_honest_capabilities(CodeLanguage.CPP),
                )
            )

        # Check PHP
        php_files = files_by_lang.get(CodeLanguage.PHP, [])
        composer_json = files_map.get("composer.json") or ""
        php_frameworks = []
        if "laravel/framework" in composer_json:
            php_frameworks.append("Laravel")
        if "symfony/" in composer_json:
            php_frameworks.append("Symfony")
        if php_files or composer_json:
            results.append(
                TechnologyDetection(
                    name="PHP",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0 if php_files else 0.85,
                    evidence=[f"{len(php_files)} PHP file(s)"] if php_files else ["Found composer.json manifest"],
                    file_paths=php_files[:10],
                    detected_frameworks=php_frameworks,
                    capabilities=get_honest_capabilities(CodeLanguage.PHP),
                )
            )

        # Check Ruby
        ruby_files = files_by_lang.get(CodeLanguage.RUBY, [])
        gemfile = files_map.get("Gemfile") or ""
        ruby_frameworks = []
        if "rails" in gemfile.lower():
            ruby_frameworks.append("Ruby on Rails")
        if ruby_files or gemfile:
            results.append(
                TechnologyDetection(
                    name="Ruby",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0 if ruby_files else 0.85,
                    evidence=[f"{len(ruby_files)} Ruby file(s)"] if ruby_files else ["Found Gemfile manifest"],
                    file_paths=ruby_files[:10],
                    detected_frameworks=ruby_frameworks,
                    capabilities=get_honest_capabilities(CodeLanguage.RUBY),
                )
            )

        # Check Kotlin
        kotlin_files = files_by_lang.get(CodeLanguage.KOTLIN, [])
        if kotlin_files:
            results.append(
                TechnologyDetection(
                    name="Kotlin",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0,
                    evidence=[f"{len(kotlin_files)} Kotlin file(s)"],
                    file_paths=kotlin_files[:10],
                    capabilities=get_honest_capabilities(CodeLanguage.KOTLIN),
                )
            )

        # Check Swift
        swift_files = files_by_lang.get(CodeLanguage.SWIFT, [])
        if swift_files:
            results.append(
                TechnologyDetection(
                    name="Swift",
                    category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                    paradigm=None,
                    confidence=1.0,
                    evidence=[f"{len(swift_files)} Swift file(s)"],
                    file_paths=swift_files[:10],
                    capabilities=get_honest_capabilities(CodeLanguage.SWIFT),
                )
            )

        # 3. Web Technologies & Data Formats (Separate from general-purpose languages)
        for web_lang, label in [
            (CodeLanguage.HTML, "HTML"),
            (CodeLanguage.CSS, "CSS"),
            (CodeLanguage.SQL, "SQL"),
            (CodeLanguage.JSON, "JSON"),
            (CodeLanguage.YAML, "YAML"),
        ]:
            files = files_by_lang.get(web_lang, [])
            if files:
                results.append(
                    TechnologyDetection(
                        name=label,
                        category=TechnologyCategory.WEB_TECHNOLOGY,
                        paradigm=None,
                        confidence=1.0,
                        evidence=[f"{len(files)} {label} file(s)"],
                        file_paths=files[:10],
                        capabilities=get_honest_capabilities(web_lang),
                    )
                )

        # 4. Deterministic Database Technology Detection (PostgreSQL, MySQL, SQLite, MongoDB)
        # Scan for connection URIs, driver packages in manifests, SQL schema files, and ORM/ODM models
        all_text = "\n".join(
            f"{path}:\n{content[:4000]}"
            for path, content in files_map.items()
            if path.endswith((
                ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".cs", ".php", ".rb",
                ".json", ".env", ".env.example", ".sql", ".yml", ".yaml", ".txt", ".toml", ".xml", ".gradle", ".mod"
            )) or os.path.basename(path) in ("Gemfile", "Makefile", "Dockerfile")
        )

        cls._detect_mysql(files_map, all_text, results)
        cls._detect_postgresql(files_map, all_text, results)
        cls._detect_sqlite(files_map, all_text, results)
        cls._detect_mongodb(files_map, all_text, results)

        return results

    @classmethod
    def _detect_mysql(cls, files_map: dict[str, str], all_text: str, results: list[TechnologyDetection]) -> None:
        """Detect MySQL relational database technology and drivers."""
        evidence: list[str] = []
        drivers: list[str] = []
        relevant_files: list[str] = []

        # Check connection strings
        mysql_uris = re.findall(r"mysql(?:\+[a-z]+)?://[^\s\"']+", all_text)
        for uri in mysql_uris:
            evidence.append(f"Found MySQL URI: {mask_credentials(uri)}")

        # Check driver packages
        mysql_driver_patterns = [
            ("mysqlclient", "Python mysqlclient"),
            ("mysql-connector-python", "Python MySQL Connector"),
            ("pymysql", "Python PyMySQL"),
            ("aiomysql", "Python aiomysql"),
            ("mysql2", "Node.js mysql2"),
            ("mysql", "Node.js mysql"),
            ("mysql-connector-j", "Java MySQL Connector/J"),
            ("go-sql-driver/mysql", "Go MySQL Driver"),
        ]
        for pkg, name in mysql_driver_patterns:
            if pkg in all_text:
                drivers.append(name)
                evidence.append(f"Detected driver: {name}")

        # Check environment variables
        if "MYSQL_DATABASE" in all_text or "MYSQL_HOST" in all_text or "MYSQL_USER" in all_text:
            evidence.append("Found MySQL environment configuration variables")

        # Check SQL schema files
        for path, content in files_map.items():
            if path.endswith(".sql"):
                if "ENGINE=InnoDB" in content or "AUTO_INCREMENT" in content or "DEFAULT CHARSET" in content:
                    evidence.append(f"MySQL schema syntax in {path}")
                    relevant_files.append(path)

        if evidence or drivers:
            results.append(
                TechnologyDetection(
                    name="MySQL",
                    category=TechnologyCategory.DATABASE_ENGINE,
                    paradigm=DatabaseParadigm.RELATIONAL,
                    confidence=1.0 if (len(evidence) > 1 or drivers) else 0.8,
                    evidence=list(dict.fromkeys(evidence)),
                    file_paths=relevant_files[:10],
                    detected_drivers=list(dict.fromkeys(drivers)),
                    capabilities=get_honest_capabilities(CodeLanguage.MYSQL),
                )
            )

    @classmethod
    def _detect_postgresql(cls, files_map: dict[str, str], all_text: str, results: list[TechnologyDetection]) -> None:
        """Detect PostgreSQL relational database technology and drivers."""
        evidence: list[str] = []
        drivers: list[str] = []
        relevant_files: list[str] = []

        # Check connection strings
        pg_uris = re.findall(r"postgres(?:ql)?(?:\+[a-z]+)?://[^\s\"']+", all_text)
        for uri in pg_uris:
            evidence.append(f"Found PostgreSQL URI: {mask_credentials(uri)}")

        # Check driver packages
        pg_driver_patterns = [
            ("psycopg2", "Python psycopg2"),
            ("asyncpg", "Python asyncpg"),
            ("psycopg", "Python psycopg 3"),
            ("pg-promise", "Node.js pg-promise"),
            ("pg", "Node.js pg"),
            ("org.postgresql", "Java PostgreSQL JDBC"),
            ("lib/pq", "Go lib/pq"),
            ("jackc/pgx", "Go pgx"),
        ]
        for pkg, name in pg_driver_patterns:
            if pkg in all_text:
                drivers.append(name)
                evidence.append(f"Detected driver: {name}")

        # Check environment variables
        if "POSTGRES_DB" in all_text or "POSTGRES_USER" in all_text or "PGDATABASE" in all_text:
            evidence.append("Found PostgreSQL environment variables")

        # Check SQL schema files
        for path, content in files_map.items():
            if path.endswith(".sql"):
                if "SERIAL" in content or "BIGSERIAL" in content or "uuid_generate_v4" in content or "timestamptz" in content.lower():
                    evidence.append(f"PostgreSQL schema syntax in {path}")
                    relevant_files.append(path)

        if evidence or drivers:
            results.append(
                TechnologyDetection(
                    name="PostgreSQL",
                    category=TechnologyCategory.DATABASE_ENGINE,
                    paradigm=DatabaseParadigm.RELATIONAL,
                    confidence=1.0 if (len(evidence) > 1 or drivers) else 0.8,
                    evidence=list(dict.fromkeys(evidence)),
                    file_paths=relevant_files[:10],
                    detected_drivers=list(dict.fromkeys(drivers)),
                    capabilities=get_honest_capabilities(CodeLanguage.POSTGRESQL),
                )
            )

    @classmethod
    def _detect_sqlite(cls, files_map: dict[str, str], all_text: str, results: list[TechnologyDetection]) -> None:
        """Detect SQLite embedded relational database technology."""
        evidence: list[str] = []
        drivers: list[str] = []
        relevant_files: list[str] = []

        sqlite_uris = re.findall(r"sqlite(?:\+[a-z]+)?:///[^\s\"']+", all_text)
        for uri in sqlite_uris:
            evidence.append(f"Found SQLite URI: {uri}")

        sqlite_drivers = [
            ("aiosqlite", "Python aiosqlite"),
            ("sqlite3", "sqlite3 driver"),
            ("better-sqlite3", "Node.js better-sqlite3"),
        ]
        for pkg, name in sqlite_drivers:
            if pkg in all_text:
                drivers.append(name)
                evidence.append(f"Detected driver: {name}")

        for path in files_map:
            if path.endswith((".sqlite", ".sqlite3", ".db")):
                evidence.append(f"Found SQLite database file: {path}")
                relevant_files.append(path)

        if evidence or drivers:
            results.append(
                TechnologyDetection(
                    name="SQLite",
                    category=TechnologyCategory.DATABASE_ENGINE,
                    paradigm=DatabaseParadigm.RELATIONAL,
                    confidence=1.0 if (len(evidence) > 1 or drivers) else 0.8,
                    evidence=list(dict.fromkeys(evidence)),
                    file_paths=relevant_files[:10],
                    detected_drivers=list(dict.fromkeys(drivers)),
                    capabilities=get_honest_capabilities(CodeLanguage.SQLITE),
                )
            )

    @classmethod
    def _detect_mongodb(cls, files_map: dict[str, str], all_text: str, results: list[TechnologyDetection]) -> None:
        """Detect MongoDB document database technology, ODMs, and aggregation pipelines."""
        evidence: list[str] = []
        drivers: list[str] = []
        relevant_files: list[str] = []

        # Check connection strings
        mongo_uris = re.findall(r"mongodb(?:\+srv)?://[^\s\"']+", all_text)
        for uri in mongo_uris:
            evidence.append(f"Found MongoDB URI: {mask_credentials(uri)}")

        # Check driver packages and ODMs
        mongo_driver_patterns = [
            ("pymongo", "Python PyMongo"),
            ("motor", "Python Motor"),
            ("mongoengine", "Python MongoEngine"),
            ("mongoose", "Node.js Mongoose ODM"),
            ("mongodb", "Node.js MongoDB driver"),
            ("mongo-driver", "Go MongoDB Driver"),
            ("spring-data-mongodb", "Spring Data MongoDB"),
        ]
        for pkg, name in mongo_driver_patterns:
            if pkg in all_text:
                drivers.append(name)
                evidence.append(f"Detected driver/ODM: {name}")

        # Check environment variables
        if "MONGODB_URI" in all_text or "MONGO_URL" in all_text or "MONGODB_DATABASE" in all_text:
            evidence.append("Found MongoDB environment configuration variables")

        # Check code patterns (Mongoose schemas, aggregation pipelines, collections)
        for path, content in files_map.items():
            if path.endswith((".js", ".ts", ".py")):
                if "new Schema({" in content or "mongoose.model(" in content:
                    evidence.append(f"Mongoose schema/model definition in {path}")
                    relevant_files.append(path)
                elif "aggregate([" in content or "$match" in content or "$group" in content or "$lookup" in content:
                    evidence.append(f"MongoDB aggregation pipeline syntax in {path}")
                    relevant_files.append(path)
                elif "createCollection" in content or "MongoClient(" in content:
                    evidence.append(f"MongoDB client/collection operation in {path}")
                    relevant_files.append(path)

        if evidence or drivers:
            results.append(
                TechnologyDetection(
                    name="MongoDB",
                    category=TechnologyCategory.DATABASE_ENGINE,
                    paradigm=DatabaseParadigm.DOCUMENT,
                    confidence=1.0 if (len(evidence) > 1 or drivers) else 0.8,
                    evidence=list(dict.fromkeys(evidence)),
                    file_paths=relevant_files[:10],
                    detected_drivers=list(dict.fromkeys(drivers)),
                    capabilities=get_honest_capabilities(CodeLanguage.MONGODB),
                )
            )
