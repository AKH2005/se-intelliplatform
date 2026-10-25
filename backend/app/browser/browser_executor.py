"""Browser Docker Container Executor for Phase 11J (Stage 3).

Responsible for executing the isolated Playwright/Chromium container on the
application's internal Docker bridge network with hardened security settings.

Security & Isolation Invariants:
1. No host port publishing (-p and --publish are forbidden).
2. Connected exclusively to the ephemeral internal network (no public internet).
3. Hardened container limits: 1024MB RAM, 1.5 CPU, 128 PIDs, 512MB shm-size.
4. Non-root user execution (pwuser, UID 1000).
5. No Docker socket (/var/run/docker.sock is NEVER mounted).
6. --security-opt=no-new-privileges:true.
7. Fixed executable invocation via asyncio.create_subprocess_exec (NEVER shell=True).
8. Guaranteed cleanup in finally blocks.
"""

import asyncio
import logging
import os
import shutil
import subprocess
from typing import Any

from app.browser.contracts import DEFAULT_PLAYWRIGHT_IMAGE, BrowserLimits
from app.browser.errors import (
    BrowserStartupError,
    BrowserTimeoutError,
)

logger = logging.getLogger(__name__)


class BrowserExecutor:
    """Dedicated Docker executor for browser container execution."""

    def __init__(self, image: str = DEFAULT_PLAYWRIGHT_IMAGE) -> None:
        self.image = image

    async def _safe_subprocess_exec(
        self,
        *cmd: str,
        capture_output: bool = True,
        timeout: float | None = None,
    ) -> tuple[int, bytes, bytes]:
        """Safely execute subprocess asynchronously, with fallback for environments lacking subprocess_exec."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
                return proc.returncode, stdout_bytes or b"", stderr_bytes or b""
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                raise
        except NotImplementedError:
            def _sync():
                try:
                    res = subprocess.run(
                        list(cmd),
                        stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                        stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                        timeout=timeout,
                        shell=False,
                    )
                    return res.returncode, res.stdout or b"", res.stderr or b""
                except subprocess.TimeoutExpired:
                    raise asyncio.TimeoutError()
            return await asyncio.to_thread(_sync)

    async def check_image_available(self, image_name: str | None = None) -> bool:
        """Verify whether the requested browser image is present locally."""
        img = image_name or self.image
        try:
            code, _, _ = await self._safe_subprocess_exec("docker", "image", "inspect", img, capture_output=False, timeout=5.0)
            return code == 0
        except Exception:
            return False

    def build_container_args(
        self,
        container_name: str,
        network_name: str,
        workspace_dir: str,
        limits: BrowserLimits,
    ) -> list[str]:
        """Construct deterministic, hardened argument vector for browser container.

        CRITICAL: Never publishes host ports (-p is forbidden).
        """
        # Convert path to forward slashes for Docker volume mounting
        normalized_workspace = os.path.abspath(workspace_dir).replace("\\", "/")

        args = [
            "run",
            "-d",
            "--name",
            container_name,
            "--hostname",
            container_name,
            "--network",
            network_name,
            f"--memory={limits.container_memory}",
            f"--cpus={limits.container_cpus}",
            f"--pids-limit={limits.container_pids}",
            f"--shm-size={limits.container_shm_size}",
            "--security-opt=no-new-privileges:true",
            "--workdir=/workspace",
            "-v",
            f"{normalized_workspace}:/workspace:rw",
            "--user",
            "1000:1000",
            self.image,
            "python",
            "/workspace/runner.py",
        ]
        return args

    async def run_browser_container(
        self,
        container_name: str,
        network_name: str,
        workspace_dir: str,
        limits: BrowserLimits,
    ) -> tuple[int, str, str]:
        """Launch the browser container, wait for completion, and return (exit_code, stdout, stderr)."""
        args = self.build_container_args(
            container_name=container_name,
            network_name=network_name,
            workspace_dir=workspace_dir,
            limits=limits,
        )

        try:
            ret, stdout_b, stderr_b = await self._safe_subprocess_exec("docker", *args)
            if ret != 0:
                err_msg = stderr_b.decode(errors="replace").strip()
                raise BrowserStartupError(f"Failed to start browser container: {err_msg}")
        except FileNotFoundError:
            raise BrowserStartupError("Docker executable not found on host.")
        except Exception as exc:
            if isinstance(exc, BrowserStartupError):
                raise
            raise BrowserStartupError(f"Error launching browser container: {exc}")

        # Wait for container execution to complete bounded by timeout
        try:
            exit_code = await self.wait_for_completion(
                container_name=container_name,
                timeout_seconds=limits.session_timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise BrowserTimeoutError(
                f"Browser container '{container_name}' exceeded timeout of {limits.session_timeout_seconds}s"
            )

        stdout, stderr = await self.get_container_logs(container_name)
        return exit_code, stdout, stderr

    async def wait_for_completion(
        self,
        container_name: str,
        timeout_seconds: float = 60.0,
    ) -> int:
        """Wait for browser container to exit with timeout."""
        try:
            _, stdout_b, _ = await self._safe_subprocess_exec(
                "docker", "wait", container_name, timeout=timeout_seconds
            )
            exit_code_str = stdout_b.decode(errors="replace").strip()
            return int(exit_code_str) if exit_code_str.isdigit() else 1
        except asyncio.TimeoutError:
            raise

    async def get_container_logs(
        self,
        container_name: str,
        tail_lines: int = 500,
    ) -> tuple[str, str]:
        """Fetch bounded container logs."""
        try:
            _, stdout_b, stderr_b = await self._safe_subprocess_exec(
                "docker", "logs", f"--tail={tail_lines}", container_name, timeout=5.0
            )
            stdout = stdout_b.decode("utf-8", errors="replace").strip()
            stderr = stderr_b.decode("utf-8", errors="replace").strip()
            return stdout, stderr
        except Exception as exc:
            logger.warning(f"Failed to fetch logs for browser container '{container_name}': {exc}")
            return "", ""

    async def stop_and_remove_container(self, container_name: str) -> None:
        """Deterministic teardown: stop container (grace period 5s) and remove."""
        try:
            await self._safe_subprocess_exec(
                "docker", "stop", "-t", "5", container_name, capture_output=False, timeout=5.0
            )
        except Exception as exc:
            logger.debug(f"Docker stop warning for '{container_name}': {exc}")

        try:
            await self._safe_subprocess_exec(
                "docker", "rm", "-f", container_name, capture_output=False, timeout=5.0
            )
        except Exception as exc:
            logger.debug(f"Docker rm warning for '{container_name}': {exc}")
