from pathlib import Path

# 1. Update preview_runtime_manager.py
prm_path = Path("backend/app/runtime/preview_runtime_manager.py")
text = prm_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_code = """    def _is_docker_available(self) -> bool:
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3.0,
            )
            return res.returncode == 0
        except Exception:
            return False"""

new_code = """    def _is_docker_available(self) -> bool:
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
        return self._docker_cached"""

if old_code in text:
    text = text.replace(old_code, new_code)
    prm_path.write_text(text, encoding="utf-8", newline="\n")
    print("Updated preview_runtime_manager.py successfully.")
else:
    print("old_code not found in preview_runtime_manager.py")

# 2. Update preview_runtime.py stop_runtime
pr_path = Path("backend/app/api/v1/endpoints/preview_runtime.py")
text_pr = pr_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_stop = """    project = await _resolve_project(project_id, session, current_user)
    preview_runtime_manager.stop_runtime(project_id=str(project_id))"""

new_stop = """    project = await _resolve_project(project_id, session, current_user)
    await asyncio.to_thread(preview_runtime_manager.stop_runtime, str(project_id))"""

if old_stop in text_pr:
    text_pr = text_pr.replace(old_stop, new_stop)
    pr_path.write_text(text_pr, encoding="utf-8", newline="\n")
    print("Updated preview_runtime.py stop_runtime successfully.")
else:
    print("old_stop not found in preview_runtime.py")

