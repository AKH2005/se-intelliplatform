"""Application Runtime Manifest and Security Contracts for Phase 11J.

This module defines the strongly-typed, deterministic data contracts for
specifying and validating application runtime metadata. The manifest is
STRICTLY DATA: it never executes commands, starts containers, or touches
the host filesystem or network.
"""

import enum
import re
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# 1. Constants & Security Rules
# ==============================================================================

# Permitted executable binaries for launching generated services
ALLOWED_EXECUTABLES: frozenset[str] = frozenset({
    "python",
    "python3",
    "uvicorn",
    "gunicorn",
})

# Disallowed environment variables that could manipulate dynamic linking or interpreter startup
PROHIBITED_ENV_VARS: frozenset[str] = frozenset({
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "PYTHONSTARTUP",
    "PYTHONEXECUTABLE",
    "PATH",
    "SUDO_USER",
    "DOCKER_HOST",
    "DOCKER_CERT_PATH",
    "DOCKER_TLS_VERIFY",
})

# Reserved ports commonly bound to critical host infrastructure services
PROHIBITED_PORTS: frozenset[int] = frozenset({
    22,     # SSH
    80,     # HTTP
    443,    # HTTPS
    2375,   # Docker daemon (unencrypted)
    2376,   # Docker daemon (TLS)
    3306,   # MySQL
    5432,   # PostgreSQL
    6379,   # Redis
    27017,  # MongoDB
})

# Entrypoint pattern: valid Python dotted module + callable (e.g. "app.main:app")
ENTRYPOINT_PATTERN = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$"
)

# Relative URL path pattern (e.g. "/docs", "/health", "/api/v1/ping")
HEALTH_PATH_PATTERN = re.compile(r"^/[a-zA-Z0-9_\-\./]*$")

# Environment variable name pattern
ENV_VAR_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")

# Shell injection patterns that must be rejected anywhere in command arguments
SHELL_METATOKENS: tuple[str, ...] = (
    ";",
    "&&",
    "||",
    "|",
    "&",
    "$",
    "`",
    ">",
    "<",
    "\n",
    "\r",
    "\x00",
)


# ==============================================================================
# 2. Enumerations
# ==============================================================================

class RuntimeLanguage(str, enum.Enum):
    """Supported programming languages for generated application runtimes."""

    PYTHON = "python"


class RuntimeFramework(str, enum.Enum):
    """Supported web application frameworks for generated application runtimes."""

    FASTAPI = "fastapi"


# ==============================================================================
# 3. ApplicationRuntimeManifest Model
# ==============================================================================

class ApplicationRuntimeManifest(BaseModel):
    """Deterministic, validated metadata specification for starting an application runtime.
    
    Invariants:
    - Pure data contract; executes no commands.
    - Application port is internal-only; no host port bindings.
    - Startup command is a validated token list; no shell chaining or substitution.
    - Health-check path is strictly relative; no external URLs or hosts.
    - Rejects path traversal, Windows drive paths, backslashes, and Docker sockets.
    """

    model_config = ConfigDict(extra="forbid")

    runtime_type: str = Field(
        default="docker",
        description="Runtime virtualization provider (currently isolated docker container)",
    )
    language: RuntimeLanguage = Field(
        default=RuntimeLanguage.PYTHON,
        description="Runtime programming language",
    )
    framework: RuntimeFramework = Field(
        default=RuntimeFramework.FASTAPI,
        description="Web application framework",
    )
    entrypoint: str = Field(
        default="app.main:app",
        min_length=3,
        max_length=100,
        description="Dotted Python module and application callable (e.g. 'app.main:app')",
    )
    startup_command: list[str] = Field(
        default_factory=lambda: [
            "python",
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        description="Structured command argument tokens executed without shell interpolation",
    )
    application_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Internal container listening port (internal Docker network only, no host binding)",
    )
    health_check_path: str = Field(
        default="/docs",
        min_length=1,
        max_length=100,
        description="Relative HTTP path for readiness polling (e.g. '/docs' or '/health')",
    )
    health_check_method: str = Field(
        default="GET",
        description="HTTP method for health check probe (GET or HEAD)",
    )
    health_check_timeout_seconds: float = Field(
        default=15.0,
        ge=1.0,
        le=60.0,
        description="Maximum seconds to poll for application readiness before marking startup failure",
    )
    environment_allowlist: list[str] = Field(
        default_factory=lambda: [
            "PYTHONPATH",
            "PYTHONDONTWRITEBYTECODE",
            "PYTHONUNBUFFERED",
        ],
        description="Permitted environment variable names passed into the runtime container",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional auxiliary runtime flags and annotations",
    )

    # --------------------------------------------------------------------------
    # Field Validators
    # --------------------------------------------------------------------------

    @field_validator("entrypoint")
    @classmethod
    def validate_entrypoint(cls, value: str) -> str:
        """Validate that entrypoint matches a valid Python module:callable pattern."""
        stripped = value.strip()
        if "\\" in stripped or "/" in stripped:
            raise ValueError(f"Entrypoint must not contain slashes or path separators: '{value}'")
        if ".." in stripped:
            raise ValueError(f"Entrypoint must not contain path traversal: '{value}'")
        if not ENTRYPOINT_PATTERN.match(stripped):
            raise ValueError(
                f"Invalid entrypoint format: '{value}'. Must match 'module.submodule:callable' (e.g. 'app.main:app')."
            )
        return stripped

    @field_validator("startup_command")
    @classmethod
    def validate_startup_command(cls, tokens: list[str]) -> list[str]:
        """Validate startup command tokens against shell injection and forbidden binaries."""
        if not tokens:
            raise ValueError("startup_command must contain at least one argument token.")
        if len(tokens) > 20:
            raise ValueError(f"startup_command contains {len(tokens)} tokens, exceeding maximum limit of 20.")

        # Check executable binary (token 0)
        executable = tokens[0].strip().lower()
        if executable not in ALLOWED_EXECUTABLES:
            raise ValueError(
                f"Forbidden executable '{tokens[0]}'. Allowed executables: {sorted(ALLOWED_EXECUTABLES)}"
            )

        # Check each argument token for length, shell metacharacters, and unsafe paths
        for idx, token in enumerate(tokens):
            if not isinstance(token, str):
                raise ValueError(f"startup_command token at index {idx} must be a string.")
            if len(token) > 200:
                raise ValueError(
                    f"startup_command token at index {idx} exceeds maximum length of 200 characters."
                )

            # Check for shell metacharacters
            for meta in SHELL_METATOKENS:
                if meta in token:
                    raise ValueError(
                        f"Unsafe shell character '{meta}' detected in startup_command token: '{token}'"
                    )

            # Check for Docker socket references
            if "docker.sock" in token.lower() or "/var/run/docker" in token.lower():
                raise ValueError(
                    f"Access to Docker socket is strictly prohibited: '{token}'"
                )

            # Check for path traversal
            if ".." in token:
                raise ValueError(
                    f"Path traversal ('..') is prohibited in startup_command token: '{token}'"
                )

            # Check for Windows drive letters (e.g. C:, D:) or backslashes
            if re.search(r"^[a-zA-Z]:", token) or "\\" in token:
                raise ValueError(
                    f"Windows drive letters and backslashes are prohibited in token: '{token}'"
                )

        return [t.strip() for t in tokens]

    @field_validator("application_port")
    @classmethod
    def validate_application_port(cls, port: int) -> int:
        """Validate application port is an unprivileged non-infrastructure port."""
        if port in PROHIBITED_PORTS:
            raise ValueError(
                f"Port {port} is a reserved infrastructure port and cannot be used for application runtime."
            )
        return port

    @field_validator("health_check_path")
    @classmethod
    def validate_health_check_path(cls, path: str) -> str:
        """Validate health check path format and prohibit external targets."""
        stripped = path.strip()
        if not stripped.startswith("/"):
            raise ValueError(f"health_check_path must start with '/': '{path}'")
        if "://" in stripped or stripped.startswith("//"):
            raise ValueError(f"health_check_path must be a relative path, not an absolute URL: '{path}'")
        if "\\" in stripped:
            raise ValueError(f"health_check_path must not contain backslashes: '{path}'")
        if ".." in stripped:
            raise ValueError(f"health_check_path must not contain path traversal: '{path}'")
        if not HEALTH_PATH_PATTERN.match(stripped):
            raise ValueError(f"health_check_path contains invalid URL characters: '{path}'")
        return stripped

    @field_validator("health_check_method")
    @classmethod
    def validate_health_check_method(cls, method: str) -> str:
        """Validate health check HTTP method."""
        normalized = method.strip().upper()
        if normalized not in ("GET", "HEAD"):
            raise ValueError(f"health_check_method must be 'GET' or 'HEAD', got '{method}'")
        return normalized

    @field_validator("environment_allowlist")
    @classmethod
    def validate_environment_allowlist(cls, env_vars: list[str]) -> list[str]:
        """Validate environment variable allowlist."""
        if len(env_vars) > 20:
            raise ValueError(f"environment_allowlist exceeds maximum limit of 20 variables.")
        clean_vars: list[str] = []
        for var in env_vars:
            stripped = var.strip()
            if not ENV_VAR_PATTERN.match(stripped):
                raise ValueError(f"Invalid environment variable name: '{var}'")
            if stripped in PROHIBITED_ENV_VARS:
                raise ValueError(f"Environment variable '{var}' is prohibited for security reasons.")
            clean_vars.append(stripped)
        return clean_vars


# ==============================================================================
# 4. Helper Factory
# ==============================================================================

def create_default_fastapi_manifest(
    port: int = 8000,
    health_path: str = "/docs",
) -> ApplicationRuntimeManifest:
    """Create a standard, validated FastAPI runtime manifest."""
    return ApplicationRuntimeManifest(
        runtime_type="docker",
        language=RuntimeLanguage.PYTHON,
        framework=RuntimeFramework.FASTAPI,
        entrypoint="app.main:app",
        startup_command=[
            "python",
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ],
        application_port=port,
        health_check_path=health_path,
        health_check_method="GET",
        health_check_timeout_seconds=15.0,
    )
