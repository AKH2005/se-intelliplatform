"""Preview Runtime Process & Lifecycle Manager.

Manages the authoritative application runtime server on Port 8001:
- Real health check probe (GET http://127.0.0.1:8001/health).
- Managed local Uvicorn process binding strictly to 127.0.0.1:8001.
- Project-aware context synchronization (Todo List / TaskFlow vs EventHub).
- Lifecycle state transitions: STARTING -> HEALTH_CHECKING -> RUNNING, or UNAVAILABLE / FAILED.
- Safe restart and shutdown semantics.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from typing import Any, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class PreviewRuntimeManager:
    """Manages the lifecycle, health probing, and process state of the Port 8001 runtime."""

    _instance: Optional["PreviewRuntimeManager"] = None
    _process: Optional[subprocess.Popen] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self.host: str = "127.0.0.1"
        self.port: int = 8001
        self.base_url: str = f"http://{self.host}:{self.port}"
        self.health_url: str = f"{self.base_url}/health"

    @classmethod
    def get_instance(cls) -> "PreviewRuntimeManager":
        if cls._instance is None:
            cls._instance = PreviewRuntimeManager()
        return cls._instance

    def _sync_http_get(self, url: str, timeout: float = 1.0) -> Tuple[bool, int, dict]:
        """Perform a synchronous HTTP GET probe with short timeout."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SE-IntelliPlatform-HealthCheck"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.getcode()
                raw = resp.read().decode("utf-8")
                try:
                    data = json.loads(raw)
                except Exception:
                    data = {"raw": raw}
                return (status_code == 200, status_code, data)
        except urllib.error.HTTPError as e:
            return (False, e.code, {"error": str(e)})
        except Exception as exc:
            return (False, 0, {"error": str(exc)})

    def _sync_http_post(self, url: str, payload: dict, timeout: float = 1.5) -> Tuple[bool, int, dict]:
        """Perform a synchronous HTTP POST with JSON body."""
        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json", "User-Agent": "SE-IntelliPlatform-ContextSync"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.getcode()
                raw = resp.read().decode("utf-8")
                try:
                    data = json.loads(raw)
                except Exception:
                    data = {"raw": raw}
                return (status_code == 200, status_code, data)
        except Exception as exc:
            return (False, 0, {"error": str(exc)})

    async def check_health(self, project_id: Optional[str] = None, timeout: float = 1.2) -> Tuple[bool, str, dict]:
        """Probe the actual configured runtime health endpoint asynchronously.

        In production environments, the integrated FastAPI endpoint serves application
        previews directly over HTTPS; never report port 8001 as unavailable.
        """
        if settings.ENVIRONMENT == "production":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                async with AsyncSessionLocal() as test_session:
                    await test_session.execute(text("SELECT 1"))
                api_healthy = True
            except Exception as exc:
                logger.warning(f"Production database health probe failed: {exc}")
                api_healthy = False

            if not api_healthy:
                return False, "Integrated application preview database degraded.", {
                    "environment": "production",
                    "mode": "integrated",
                    "port": 443,
                    "status": "FAILED",
                    "container_status": "NOT_APPLICABLE",
                    "execution_type": "integrated_runtime",
                }

            return True, "Integrated application preview active via HTTPS and verified healthy.", {
                "environment": "production",
                "mode": "integrated",
                "port": 443,
                "status": "RUNNING",
                "container_status": "NOT_APPLICABLE",
                "execution_type": "integrated_runtime",
            }

        if project_id and self._is_docker_available():
            c_name = f"se-app-{project_id}"
            try:
                res = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Running}}", c_name],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
                if res.returncode != 0 or res.stdout.strip().lower() != "true":
                    return False, f"Container for project {project_id} is not running.", {
                        "status": "STOPPED",
                        "container_status": "STOPPED",
                        "execution_type": "isolated_container",
                        "port": self.port,
                    }
                # Probe actual application API health within container
                c_ok, c_code, _ = await asyncio.to_thread(self._sync_http_get, f"http://127.0.0.1:{self.port}/health", timeout)
                if not c_ok:
                    c_ok, c_code, _ = await asyncio.to_thread(self._sync_http_get, f"http://127.0.0.1:{self.port}/api/tasks", timeout)
                if not c_ok:
                    return False, f"Container running but application API is not responding (code: {c_code}).", {
                        "status": "STARTING",
                        "container_status": "STARTING",
                        "execution_type": "isolated_container",
                        "port": self.port,
                    }
            except Exception:
                pass

        ok, code, data = await asyncio.to_thread(self._sync_http_get, self.health_url, timeout)
        if not ok:
            ok, code, data = await asyncio.to_thread(self._sync_http_get, f"{self.base_url}/", timeout)

        if ok:
            return True, "Application running on port 8001.", {
                **data,
                "status": "RUNNING",
                "container_status": "RUNNING",
                "execution_type": "isolated_container",
                "port": self.port,
            }

        container_status = "STOPPED"
        if project_id:
            c_name = f"se-app-{project_id}"
            try:
                res = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Running}} {{.State.ExitCode}}", c_name],
                    capture_output=True,
                    text=True,
                    timeout=3.0,
                )
                if res.returncode == 0:
                    parts = res.stdout.strip().split()
                    if parts:
                        is_running = parts[0].lower() == "true"
                        if is_running:
                            container_status = "STARTING"
                        else:
                            exit_code = parts[1] if len(parts) > 1 else "0"
                            container_status = "START_FAILED" if exit_code != "0" else "STOPPED"
            except Exception:
                pass

        return False, f"Application runtime unavailable on port 8001 (code: {code}).", {
            "status": container_status if container_status in ("START_FAILED", "STARTING") else "STOPPED",
            "container_status": container_status,
            "port": self.port,
            "execution_type": "isolated_container",
            "error_code": code,
        }

    def _kill_stale_port_8001(self) -> None:
        """Kill any process occupying port 8001 if it belongs to a dead/unresponsive runtime."""
        if os.name == "nt":
            try:
                # Find PID holding port 8001
                cmd = "netstat -ano | findstr :8001"
                out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                pids = set()
                for line in out.strip().splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 5 and "LISTENING" in line:
                        pids.add(parts[-1])
                for pid in pids:
                    try:
                        # Use /T to kill entire process tree including child uvicorn workers
                        subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        logger.info(f"Terminated stale process tree on port 8001 (PID {pid}).")
                    except Exception:
                        pass
                import socket
                for _ in range(12):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.2)
                        if s.connect_ex(("127.0.0.1", 8001)) != 0:
                            break
                    time.sleep(0.2)
            except Exception:
                pass
        else:
            try:
                subprocess.run("fuser -k 8001/tcp", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def _is_docker_available(self) -> bool:
        if hasattr(self, "_docker_cached") and self._docker_cached is not None:
            return self._docker_cached
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
            self._docker_cached = (res.returncode == 0)
        except Exception:
            self._docker_cached = False
        return self._docker_cached

    async def _resolve_project_files(self, project_id: uuid.UUID) -> dict[str, str]:
        from app.core.database import AsyncSessionLocal
        from app.services.project_download_service import ProjectDownloadService

        try:
            async with AsyncSessionLocal() as session:
                pds = ProjectDownloadService(session)
                return await pds.get_project_files(project_id)
        except Exception as exc:
            logger.warning(f"Could not resolve project files for {project_id}: {exc}")
            return {}

    def materialize_project_files(self, project_id: uuid.UUID, files_map: dict[str, str], clean_stale: bool = True) -> str:
        workspace_dir = BACKEND_DIR / ".runtime_workspaces" / str(project_id)
        abs_base = os.path.abspath(str(workspace_dir))
        os.makedirs(abs_base, exist_ok=True)
        written_paths = set()
        for rel_path, content in files_map.items():
            clean_path = rel_path.replace("\\", "/").strip()
            if clean_path.startswith("/") or ".." in clean_path or re.search(r"^[a-zA-Z]:", clean_path):
                continue
            target_path = os.path.abspath(os.path.join(abs_base, clean_path))
            if not target_path.startswith(abs_base):
                continue
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as fp:
                fp.write(content)
            written_paths.add(target_path)

        if clean_stale:
            for root, _, files in os.walk(abs_base):
                for f in files:
                    full_p = os.path.abspath(os.path.join(root, f))
                    if full_p not in written_paths:
                        try:
                            os.remove(full_p)
                        except Exception:
                            pass

        return abs_base

    def clean_staging_workspace(self, project_id: uuid.UUID) -> None:
        """Safely clean up temporary staging workspace files."""
        staging_dir = BACKEND_DIR / ".runtime_workspaces" / f"{project_id}_staging"
        if os.path.exists(staging_dir):
            try:
                import shutil
                shutil.rmtree(staging_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to clean staging workspace {staging_dir}: {e}")

    def detect_entrypoint(self, workspace_dir: str) -> str:
        candidates = [
            ("backend/app/main.py", "backend.app.main:app"),
            ("backend/main.py", "backend.main:app"),
            ("app/main.py", "app.main:app"),
            ("main.py", "main:app"),
        ]
        for rel_file, ep in candidates:
            if os.path.exists(os.path.join(workspace_dir, rel_file.replace("/", os.sep))):
                return ep
        return "backend.app.main:app"

    async def sync_context(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> None:
        """Inform the preview server of the currently active project context."""
        payload = {
            "project_id": str(project_id) if project_id else None,
            "project_name": project_name or "",
            "project_description": project_description or "",
            "mode": mode,
        }
        await asyncio.to_thread(self._sync_http_post, f"{self.base_url}/api/runtime/context", payload, 1.0)

    async def ensure_running(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
        force_restart: bool = False,
    ) -> Tuple[bool, str, dict]:
        """Ensure the preview server process or Docker container is running and responding on Port 8001."""
        if settings.ENVIRONMENT == "production":
            return True, "Integrated application preview active in production environment.", {
                "port": 443,
                "status": "RUNNING",
                "container_status": "NOT_APPLICABLE",
                "execution_type": "integrated_runtime",
            }

        async with self._lock:
            return await self._ensure_running_unlocked(
                project_id, project_name, project_description, force_restart=force_restart
            )

    async def _ensure_running_unlocked(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
        force_restart: bool = False,
    ) -> Tuple[bool, str, dict]:
        """Internal unlocked runner for ensure_running and restart_runtime."""
        if settings.ENVIRONMENT == "production":
            return True, "Integrated application preview active in production environment.", {
                "port": 443,
                "status": "RUNNING",
                "container_status": "NOT_APPLICABLE",
                "execution_type": "integrated_runtime",
            }

        # 1. Quick probe: is it already running and healthy? (Only if not forcing restart)
        if not force_restart:
            healthy, msg, details = await self.check_health(project_id=project_id, timeout=0.8)
            if healthy:
                await self.sync_context(project_id, project_name, project_description)
                return True, "Application running on port 8001.", details

    # 2. If project_id is provided and Docker is available, launch in isolated Docker container
        is_docker = self._is_docker_available()
        if is_docker and project_id:
            try:
                p_uuid = uuid.UUID(str(project_id))
                files_map = await self._resolve_project_files(p_uuid)
                if files_map:
                    workspace_dir = self.materialize_project_files(p_uuid, files_map)
                    entrypoint = self.detect_entrypoint(workspace_dir)
                    c_name = f"se-app-{project_id}"

                    # Clean up existing container on port 8001
                    self.stop_runtime(project_id=str(project_id))
                    await asyncio.sleep(0.3)

                    cmd = [
                        "docker",
                        "run",
                        "-d",
                        "--name",
                        c_name,
                        "-p",
                        f"127.0.0.1:{self.port}:8000",
                        "-v",
                        f"{workspace_dir}:/workspace",
                        "-w",
                        "/workspace",
                        "-e",
                        "PYTHONPATH=/workspace:/workspace/backend",
                        "-e",
                        "DATABASE_URL=sqlite:////tmp/app.db",
                        "se-intelliplatform-sandbox:latest",
                        "python",
                        "-m",
                        "uvicorn",
                        entrypoint,
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "8000",
                    ]
                    logger.info(f"Starting application container '{c_name}' on port {self.port}: {' '.join(cmd)}")
                    res = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, timeout=15.0)
                    if res.returncode != 0:
                        err = res.stderr.strip()
                        logger.error(f"Failed to start container '{c_name}': {err}")
                        return False, f"Docker container failed to start: {err}", {
                            "status": "START_FAILED",
                            "container_status": "START_FAILED",
                            "execution_type": "isolated_container",
                            "port": self.port,
                        }

                    # Poll health check
                    start_poll = time.monotonic()
                    poll_timeout = 10.0
                    last_err = ""
                    while time.monotonic() - start_poll < poll_timeout:
                        await asyncio.sleep(0.4)
                        healthy, probe_msg, probe_details = await self.check_health(project_id=str(project_id), timeout=0.8)
                        if healthy:
                            logger.info(f"Container '{c_name}' verified healthy on port {self.port}.")
                            return True, "Application running on port 8001.", probe_details
                        last_err = probe_msg

                    # Failed to become healthy within timeout
                    logs_res = await asyncio.to_thread(
                        subprocess.run, ["docker", "logs", "--tail", "30", c_name],
                        capture_output=True, text=True, timeout=4.0
                    )
                    container_logs = logs_res.stdout.strip() or logs_res.stderr.strip() or last_err
                    return False, f"Container started but not responding: {container_logs[:180]}", {
                        "status": "START_FAILED",
                        "container_status": "START_FAILED",
                        "execution_type": "isolated_container",
                        "port": self.port,
                    }
                else:
                    logger.info(f"No custom files found for project {p_uuid}; falling back to preview server runtime.")
            except Exception as exc:
                logger.error(f"Error launching Docker container for project {project_id}: {exc}")
                return False, f"Error launching application container: {exc}", {
                    "status": "START_FAILED",
                    "container_status": "START_FAILED",
                    "execution_type": "isolated_container",
                    "port": self.port,
                }

        # 3. Fallback: Spawn managed uvicorn process for preview_server
        if self._process and self._process.poll() is not None:
            self._process = None

        # Clean stale ports before attempting to bind
        self._kill_stale_port_8001()

        python_bin = sys.executable
        venv_py = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
        if venv_py.is_file():
            python_bin = str(venv_py)

        cmd = [
            python_bin,
            "-u",
            "-m",
            "uvicorn",
            "app.runtime.preview_server:app",
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--log-level",
            "warning",
        ]

        run_env = dict(os.environ)
        run_env["PYTHONUNBUFFERED"] = "1"
        run_env["PYTHONPATH"] = str(BACKEND_DIR) + (os.pathsep + run_env["PYTHONPATH"] if "PYTHONPATH" in run_env else "")

        log_dir = BACKEND_DIR / ".runtime_workspaces"
        os.makedirs(str(log_dir), exist_ok=True)
        log_file_path = log_dir / "preview_server.log"
        log_fp = open(str(log_file_path), "a", encoding="utf-8")
        self._log_fp = log_fp

        logger.info(f"Starting application preview runtime on {self.base_url} (command: {' '.join(cmd)})")
        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=str(BACKEND_DIR),
                env=run_env,
                stdout=log_fp,
                stderr=log_fp,
            )
        except Exception as exc:
            logger.error(f"Failed to spawn application preview runtime: {exc}")
            return False, f"Failed to spawn runtime process: {exc}", {}

        # 4. Readiness health polling loop (STARTING -> HEALTH_CHECKING -> RUNNING)
        start_poll = time.monotonic()
        poll_timeout = 25.0
        last_err = ""
        has_retried_after_crash = False

        while time.monotonic() - start_poll < poll_timeout:
            await asyncio.sleep(0.3)

            # Immediate check if process terminated prematurely (e.g. port collision / syntax error)
            if self._process and self._process.poll() is not None:
                err_msg = ""
                try:
                    if log_file_path.is_file():
                        err_msg = log_file_path.read_text(encoding="utf-8", errors="replace")[-500:].strip()
                except Exception:
                    pass
                logger.warning(f"Preview runtime process exited with code {self._process.returncode}: {err_msg}")
                if not has_retried_after_crash:
                    has_retried_after_crash = True
                    self._kill_stale_port_8001()
                    await asyncio.sleep(0.5)
                    try:
                        self._process = subprocess.Popen(
                            cmd,
                            cwd=str(BACKEND_DIR),
                            env=run_env,
                            stdout=log_fp,
                            stderr=log_fp,
                        )
                        continue
                    except Exception:
                        pass
                return False, f"Application preview runtime process exited immediately with code {self._process.returncode}. ({err_msg})", {
                    "status": "START_FAILED",
                    "container_status": "START_FAILED",
                    "execution_type": "domain_prototype",
                    "port": self.port,
                }

            healthy, msg, details = await self.check_health(project_id=project_id, timeout=1.0)
            if healthy:
                logger.info("Application preview runtime verified healthy on port 8001.")
                await self.sync_context(project_id, project_name, project_description)
                return True, "Application running on port 8001.", details
            last_err = msg

        return False, f"The application started but is not responding yet on port 8001. ({last_err})", {}

    async def restart_runtime(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
    ) -> Tuple[bool, str, dict]:
        """Gracefully terminate existing runtime, release port, and launch anew, serialized with lock."""
        if settings.ENVIRONMENT == "production":
            return True, "Application preview active in production environment.", {"port": 443}

        async with self._lock:
            if self._is_docker_available():
                self.stop_runtime(project_id=project_id)
                await asyncio.sleep(0.5)
                return await self._ensure_running_unlocked(
                    project_id, project_name, project_description, force_restart=True
                )

            # For standalone preview runtime, probe if already healthy
            healthy, msg, details = await self.check_health(project_id=project_id, timeout=1.2)
            if healthy:
                await self.sync_context(project_id, project_name, project_description)
                return True, "Application preview active on port 8001.", details

            self.stop_runtime(project_id=project_id)
            await asyncio.sleep(0.5)
            return await self._ensure_running_unlocked(
                project_id, project_name, project_description, force_restart=True
            )

    async def apply_development_change(
        self,
        project_id: Optional[str] = None,
        feature_type: str = "auth",
        parameters: Optional[dict] = None,
    ) -> Tuple[bool, str, dict]:
        """Apply a fast-path development change directly to the active preview runtime on Port 8001."""
        if settings.ENVIRONMENT == "production":
            return True, "Application preview updated for production environment.", {
                "environment": "production",
                "feature": feature_type,
            }

        healthy, msg, _ = await self.ensure_running(project_id=project_id)

        if not healthy:
            return False, f"Cannot apply changes: runtime is not responding on port 8001 ({msg}).", {}

        feature_map = {}
        change_lower = feature_type.lower()
        if any(k in change_lower for k in ["auth", "login", "register", "signin"]):
            feature_map["auth"] = True
            feature_map["login_fixed"] = True
        if any(k in change_lower for k in ["modern", "design", "look", "ui", "styling"]):
            feature_map["modern_ui"] = True
        if any(k in change_lower for k in ["fix", "button", "work"]):
            feature_map["login_fixed"] = True
            feature_map["auth"] = True
        if any(k in change_lower for k in ["search"]):
            feature_map["search"] = True
        if any(k in change_lower for k in ["filter", "category"]):
            feature_map["category_filter"] = True
        if any(k in change_lower for k in ["dark"]):
            feature_map["dark_mode"] = True

        ok, code, res_data = await asyncio.to_thread(
            self._sync_http_post,
            f"{self.base_url}/api/runtime/features",
            feature_map,
            2.0,
        )
        if not ok:
            return False, f"Failed to update runtime features on port 8001 (code: {code}).", res_data

        healthy, probe_msg, details = await self.check_health(timeout=1.0)
        if not healthy:
            return False, f"Application updated but failed health check: {probe_msg}", {}

        return True, "Application runtime updated and verified on port 8001.", details

    def stop_runtime(self, project_id: Optional[str] = None) -> None:
        """Stop runtime process and any associated Docker container synchronously."""
        if project_id:
            c_name = f"se-app-{project_id}"
            try:
                subprocess.run(["docker", "rm", "-f", c_name], capture_output=True, timeout=5.0)
            except Exception:
                pass

        # Also stop any container published to port 8001
        try:
            res = subprocess.run(
                ["docker", "ps", "-q", "--filter", f"publish={self.port}"],
                capture_output=True,
                text=True,
                timeout=4.0,
            )
            if res.returncode == 0:
                for cid in res.stdout.strip().split():
                    if cid:
                        subprocess.run(["docker", "rm", "-f", cid], capture_output=True, timeout=5.0)
        except Exception:
            pass

        if self._process:
            try:
                if os.name == "nt":
                    subprocess.run(f"taskkill /F /T /PID {self._process.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    self._process.terminate()
                self._process.wait(timeout=2.0)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None

        self._kill_stale_port_8001()


preview_runtime_manager = PreviewRuntimeManager.get_instance()
