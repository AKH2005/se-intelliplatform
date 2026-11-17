from app.runtime.preview_server import get_app_html_for_project
from pathlib import Path

pid = "68289eab-12f4-4602-a4b7-143f29c52c58"
ws_dir = Path(".").resolve() / ".runtime_workspaces" / pid
print("ws_dir exists:", ws_dir.exists())

html = get_app_html_for_project(project_id=pid)
print("html length:", len(html))
print("html snippet:", html[:300])
