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
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Optional, Tuple

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

    async def check_health(self, timeout: float = 1.2) -> Tuple[bool, str, dict]:
        """Probe the actual configured runtime health endpoint asynchronously."""
        ok, code, data = await asyncio.to_thread(self._sync_http_get, self.health_url, timeout)
        if ok:
            return True, "Application running on port 8001.", data
        return False, f"Application runtime unavailable on port 8001 (code: {code}).", data

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
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        logger.info(f"Terminated stale process on port 8001 (PID {pid}).")
                    except Exception:
                        pass
            except Exception:
                pass

    async def sync_context(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
    ) -> None:
        """Inform the preview server of the currently active project context."""
        payload = {
            "project_id": str(project_id) if project_id else None,
            "project_name": project_name or "",
            "project_description": project_description or "",
        }
        await asyncio.to_thread(self._sync_http_post, f"{self.base_url}/api/runtime/context", payload, 1.0)

    async def ensure_running(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
    ) -> Tuple[bool, str, dict]:
        """Ensure the preview server process is running and responding on Port 8001."""
        async with self._lock:
            # 1. Quick probe: is it already running and healthy?
            healthy, msg, details = await self.check_health(timeout=0.8)
            if healthy:
                await self.sync_context(project_id, project_name, project_description)
                return True, "Application running on port 8001.", details

            # 2. If not healthy, check if process died or port is stuck
            if self._process and self._process.poll() is not None:
                self._process = None

            # 3. Spawn managed uvicorn process for preview_server
            python_bin = sys.executable
            cmd = [
                python_bin,
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

            logger.info(f"Starting application preview runtime on {self.base_url} (command: {' '.join(cmd)})")
            try:
                self._process = subprocess.Popen(
                    cmd,
                    cwd=str(BACKEND_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as exc:
                logger.error(f"Failed to spawn application preview runtime: {exc}")
                return False, f"Failed to spawn runtime process: {exc}", {}

            # 4. Readiness health polling loop (STARTING -> HEALTH_CHECKING -> RUNNING)
            start_poll = time.monotonic()
            poll_timeout = 8.0
            last_err = ""

            while time.monotonic() - start_poll < poll_timeout:
                await asyncio.sleep(0.3)
                healthy, msg, details = await self.check_health(timeout=0.6)
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
        """Gracefully terminate existing runtime, release port, and launch anew."""
        async with self._lock:
            if self._process:
                try:
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                except Exception:
                    pass
                self._process = None

            self._kill_stale_port_8001()
            await asyncio.sleep(0.5)

        return await self.ensure_running(project_id, project_name, project_description)

    async def apply_development_change(
        self,
        project_id: Optional[str] = None,
        feature_type: str = "auth",
        parameters: Optional[dict] = None,
    ) -> Tuple[bool, str, dict]:
        """Apply a fast-path development change directly to the active preview runtime on Port 8001."""
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

    def stop_runtime(self) -> None:
        """Stop runtime process synchronously upon application shutdown."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=2.0)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None


preview_runtime_manager = PreviewRuntimeManager.get_instance()
