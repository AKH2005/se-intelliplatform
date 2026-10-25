"""Unit Tests for ApplicationRuntimeManifest and Security Contracts (Phase 11J - Stage 1)."""

import pytest
from pydantic import ValidationError

from app.schemas.runtime import (
    ApplicationRuntimeManifest,
    RuntimeFramework,
    RuntimeLanguage,
    create_default_fastapi_manifest,
)


class TestApplicationRuntimeManifestValidCases:
    """Test valid permutations of ApplicationRuntimeManifest."""

    def test_default_manifest_is_valid(self):
        manifest = ApplicationRuntimeManifest()
        assert manifest.runtime_type == "docker"
        assert manifest.language == RuntimeLanguage.PYTHON
        assert manifest.framework == RuntimeFramework.FASTAPI
        assert manifest.entrypoint == "app.main:app"
        assert manifest.application_port == 8000
        assert manifest.health_check_path == "/docs"
        assert manifest.health_check_method == "GET"
        assert manifest.health_check_timeout_seconds == 15.0
        assert "PYTHONPATH" in manifest.environment_allowlist
        assert manifest.startup_command[0] == "python"

    def test_factory_helper_creates_valid_manifest(self):
        manifest = create_default_fastapi_manifest(port=8080, health_path="/health")
        assert manifest.application_port == 8080
        assert manifest.health_check_path == "/health"
        assert manifest.startup_command[-1] == "8080"
        assert manifest.entrypoint == "app.main:app"

    def test_custom_valid_entrypoint_and_port(self):
        manifest = ApplicationRuntimeManifest(
            entrypoint="my_package.api_service:application",
            application_port=3000,
            health_check_path="/api/v1/health",
            health_check_method="HEAD",
            health_check_timeout_seconds=5.0,
            environment_allowlist=["APP_ENV", "LOG_LEVEL"],
        )
        assert manifest.entrypoint == "my_package.api_service:application"
        assert manifest.application_port == 3000
        assert manifest.health_check_method == "HEAD"
        assert "APP_ENV" in manifest.environment_allowlist

    def test_valid_executables(self):
        for exe in ("python", "python3", "uvicorn", "gunicorn"):
            manifest = ApplicationRuntimeManifest(
                startup_command=[exe, "--help"]
            )
            assert manifest.startup_command[0] == exe


class TestApplicationRuntimeManifestSecurityConstraints:
    """Test deterministic security constraints, rejection of shell injection, and boundary enforcement."""

    def test_reject_extra_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            ApplicationRuntimeManifest(arbitrary_injected_field="malicious_payload")  # type: ignore[call-arg]
        assert "extra_forbidden" in str(exc_info.value)

    # --------------------------------------------------------------------------
    # Entrypoint Security
    # --------------------------------------------------------------------------

    @pytest.mark.parametrize("bad_entrypoint", [
        "app/main:app",            # slashes
        "app\\main:app",           # backslashes
        "../main:app",             # traversal
        "C:\\app.main:app",        # Windows drive
        "app.main",                # missing callable colon
        ":app",                    # missing module
        "app.main:app;rm -rf /",   # command chaining attempt
        "app.main:$app",           # variable substitution attempt
        "app.main:app`id`",        # backtick substitution
        "   ",                     # empty
    ])
    def test_reject_invalid_entrypoints(self, bad_entrypoint: str):
        with pytest.raises(ValidationError):
            ApplicationRuntimeManifest(entrypoint=bad_entrypoint)

    # --------------------------------------------------------------------------
    # Startup Command Security
    # --------------------------------------------------------------------------

    def test_reject_empty_startup_command(self):
        with pytest.raises(ValidationError) as exc_info:
            ApplicationRuntimeManifest(startup_command=[])
        assert "at least one argument token" in str(exc_info.value)

    @pytest.mark.parametrize("prohibited_executable", [
        "sh",
        "bash",
        "zsh",
        "sudo",
        "docker",
        "curl",
        "wget",
        "nc",
        "rm",
        "eval",
        "powershell",
        "cmd.exe",
    ])
    def test_reject_prohibited_executables(self, prohibited_executable: str):
        with pytest.raises(ValidationError) as exc_info:
            ApplicationRuntimeManifest(startup_command=[prohibited_executable, "-c", "echo 1"])
        assert "Forbidden executable" in str(exc_info.value)

    @pytest.mark.parametrize("malicious_token", [
        "app.main:app;cat /etc/passwd",
        "app.main:app&&echo 1",
        "app.main:app||echo 1",
        "app.main:app|grep secret",
        "app.main:app&",
        "app.main:app`whoami`",
        "app.main:app$(id)",
        "${DOCKER_SECRET}",
        ">/workspace/leak.txt",
        "<input.txt",
        "token\nwith_newline",
        "token\rwith_return",
        "/var/run/docker.sock",
        "foo/docker.sock",
        "../traversal",
        "C:\\Windows\\System32",
        "C:command",
        "with\\backslash",
    ])
    def test_reject_shell_metacharacters_in_command_tokens(self, malicious_token: str):
        with pytest.raises(ValidationError):
            ApplicationRuntimeManifest(
                startup_command=["python", "-m", "uvicorn", malicious_token]
            )

    def test_reject_excessive_command_tokens(self):
        tokens = ["python"] + [f"--arg{i}" for i in range(25)]
        with pytest.raises(ValidationError) as exc_info:
            ApplicationRuntimeManifest(startup_command=tokens)
        assert "exceeding maximum limit of 20" in str(exc_info.value)

    def test_reject_oversized_single_token(self):
        oversized = "a" * 250
        with pytest.raises(ValidationError) as exc_info:
            ApplicationRuntimeManifest(startup_command=["python", oversized])
        assert "exceeds maximum length of 200" in str(exc_info.value)

    # --------------------------------------------------------------------------
    # Port Security
    # --------------------------------------------------------------------------

    @pytest.mark.parametrize("bad_port", [
        -1,
        0,
        80,     # privileged
        443,    # privileged
        22,     # SSH
        5432,   # host postgres
        6379,   # host redis
        2375,   # docker socket
        2376,   # docker tls
        70000,  # exceeds 65535
    ])
    def test_reject_unsafe_or_privileged_ports(self, bad_port: int):
        with pytest.raises(ValidationError):
            ApplicationRuntimeManifest(application_port=bad_port)

    # --------------------------------------------------------------------------
    # Health Check Security
    # --------------------------------------------------------------------------

    @pytest.mark.parametrize("bad_health_path", [
        "docs",                         # missing leading slash
        "http://localhost:8000/docs",   # absolute URL attempt
        "https://external.com/docs",    # external URL attempt
        "//169.254.169.254/meta",       # cloud metadata SSRF attempt
        "/docs/../secret",              # path traversal
        "/docs\\health",                # backslash
        "/docs?query=foo#frag",         # query/fragment characters
        "/" + "a" * 120,                # excessive length
    ])
    def test_reject_unsafe_health_check_paths(self, bad_health_path: str):
        with pytest.raises(ValidationError):
            ApplicationRuntimeManifest(health_check_path=bad_health_path)

    @pytest.mark.parametrize("bad_method", ["POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    def test_reject_unsafe_health_check_methods(self, bad_method: str):
        with pytest.raises(ValidationError) as exc_info:
            ApplicationRuntimeManifest(health_check_method=bad_method)
        assert "must be 'GET' or 'HEAD'" in str(exc_info.value)

    @pytest.mark.parametrize("bad_timeout", [0.5, 0.0, -5.0, 75.0])
    def test_reject_out_of_bounds_health_check_timeouts(self, bad_timeout: float):
        with pytest.raises(ValidationError):
            ApplicationRuntimeManifest(health_check_timeout_seconds=bad_timeout)

    # --------------------------------------------------------------------------
    # Environment Variable Security
    # --------------------------------------------------------------------------

    @pytest.mark.parametrize("prohibited_var", [
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "PYTHONSTARTUP",
        "PYTHONEXECUTABLE",
        "PATH",
        "DOCKER_HOST",
    ])
    def test_reject_dangerous_environment_variables(self, prohibited_var: str):
        with pytest.raises(ValidationError) as exc_info:
            ApplicationRuntimeManifest(environment_allowlist=[prohibited_var])
        assert "prohibited for security reasons" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_var_name", [
        "lower_case_var",
        "VAR-WITH-HYPHEN",
        "VAR WITH SPACE",
        "VAR;INJECTION",
    ])
    def test_reject_invalid_environment_variable_format(self, invalid_var_name: str):
        with pytest.raises(ValidationError):
            ApplicationRuntimeManifest(environment_allowlist=[invalid_var_name])

    def test_reject_excessive_environment_variables(self):
        many_vars = [f"CUSTOM_VAR_{i}" for i in range(25)]
        with pytest.raises(ValidationError) as exc_info:
            ApplicationRuntimeManifest(environment_allowlist=many_vars)
        assert "exceeds maximum limit of 20" in str(exc_info.value)
