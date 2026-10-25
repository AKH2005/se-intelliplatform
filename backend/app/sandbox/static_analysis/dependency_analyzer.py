"""Deterministic Import and Dependency Analysis comparing code imports vs stdlib and requirements.txt."""

import logging
import re
from typing import Any

from app.sandbox.static_analysis.ast_analyzer import ParsedModuleData
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticDiagnostic,
)

logger = logging.getLogger(__name__)

# Standard library module catalog (Python 3.10 - 3.12 standard modules)
PYTHON_STDLIB_MODULES: frozenset[str] = frozenset({
    "abc", "argparse", "array", "ast", "asyncio", "atexit", "base64", "bdb", "binascii",
    "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd",
    "code", "codecs", "codeop", "collections", "colorsys", "compileall", "concurrent",
    "configparser", "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt",
    "csv", "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib",
    "dis", "distutils", "doctest", "email", "encodings", "ensurepip", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "fractions", "ftplib",
    "functools", "gc", "getopt", "getpass", "gettext", "glob", "graphlib", "gzip",
    "hashlib", "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr", "imp",
    "importlib", "inspect", "io", "ipaddress", "itertools", "json", "keyword", "lib2to3",
    "linecache", "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
    "mimetypes", "mmap", "modulefinder", "msilib", "msvcrt", "multiprocessing", "netrc",
    "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev", "pathlib", "pdb",
    "pickle", "pickletools", "pipes", "pkgutil", "platform", "plistlib", "poplib", "posix",
    "posixpath", "pprint", "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
    "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib", "resource", "rlcompleter",
    "runpy", "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil", "signal",
    "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "spwd", "sqlite3", "ssl",
    "stat", "statistics", "string", "stringprep", "struct", "subprocess", "sunau", "symtable",
    "sys", "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile", "termios",
    "test", "textwrap", "threading", "time", "timeit", "tkinter", "token", "tokenize",
    "tomllib", "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types",
    "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings", "wave",
    "weakref", "webbrowser", "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib", "_thread",
})

# Well-known import-to-package name mappings
PACKAGE_NAME_ALIASES: dict[str, str] = {
    "dotenv": "python-dotenv",
    "yaml": "pyyaml",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "bs4": "beautifulsoup4",
    "jwt": "pyjwt",
    "dateutil": "python-dateutil",
}


class DependencyAnalyzer:
    """Validates third-party module imports against declared requirements.txt entries."""

    def parse_requirements(self, content: str) -> set[str]:
        """Extract normalized package names from requirements.txt content."""
        packages: set[str] = set()
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Strip environment markers (e.g. ; sys_platform == 'linux')
            line = line.split(";")[0].strip()

            # Extract base package name before any version specifier
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)", line)
            if match:
                pkg_name = match.group(1).lower().replace("_", "-")
                packages.add(pkg_name)

        return packages

    def analyze(
        self,
        modules: list[ParsedModuleData],
        all_file_paths: list[str],
        requirements_content: str | None,
    ) -> list[StaticDiagnostic]:
        """Compare project imports against standard library, local modules, and requirements.txt."""
        diagnostics: list[StaticDiagnostic] = []

        # Identify internal project root namespaces
        internal_roots: set[str] = set()
        for path in all_file_paths:
            parts = path.strip("/").split("/")
            if parts:
                internal_roots.add(parts[0].replace(".py", ""))

        declared_packages: set[str] = set()
        if requirements_content is not None:
            declared_packages = self.parse_requirements(requirements_content)
        else:
            diagnostics.append(
                StaticDiagnostic(
                    category=DiagnosticCategory.STRUCTURE,
                    severity=DiagnosticSeverity.WARNING,
                    code="STRUCT_MISSING_REQUIREMENTS",
                    message="Project does not contain a requirements.txt dependency manifest.",
                    source="dependency_analyzer",
                )
            )

        seen_missing: set[tuple[str, str]] = set()

        for mod in modules:
            for mod_name, _imported_names, line_no in mod.imports:
                if not mod_name or mod_name.startswith("."):
                    continue  # Relative import

                # Extract top-level module name (e.g. 'app.services.user' -> 'app')
                top_level = mod_name.split(".")[0]

                # 1. Check if Standard Library
                if top_level in PYTHON_STDLIB_MODULES:
                    continue

                # 2. Check if Internal project package / module
                if top_level in internal_roots:
                    continue

                # 3. Check third-party dependency
                normalized_dep = top_level.lower().replace("_", "-")
                canonical_pkg = PACKAGE_NAME_ALIASES.get(top_level, normalized_dep)

                if canonical_pkg not in declared_packages and normalized_dep not in declared_packages:
                    key = (mod.file_path, top_level)
                    if key not in seen_missing:
                        seen_missing.add(key)
                        diagnostics.append(
                            StaticDiagnostic(
                                category=DiagnosticCategory.DEPENDENCY,
                                severity=DiagnosticSeverity.WARNING,
                                code="DEP_MISSING",
                                message=(
                                    f"Module '{top_level}' is imported in '{mod.file_path}' "
                                    f"but is not declared in requirements.txt."
                                ),
                                file_path=mod.file_path,
                                line=line_no,
                                source="dependency_analyzer",
                                evidence=f"import {mod_name}",
                                metadata={"missing_package": canonical_pkg},
                            )
                        )

        return diagnostics
