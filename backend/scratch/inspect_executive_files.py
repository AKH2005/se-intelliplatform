import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
c = conn.cursor()

pid_hex = 'd8dc84956b8a4fe3940a2b436d475454'
c.execute("select id, name, slug, settings from projects where id = ?", (pid_hex,))
proj = c.fetchone()
print("Project:", proj[0], proj[1], proj[3])

c.execute("select id, version_number, status, files_manifest, metadata from development_versions where project_id = ? order by version_number desc", (pid_hex,))
versions = c.fetchall()
for v in versions:
    v_id = v[0]
    v_num = v[1]
    v_status = v[2]
    meta = json.loads(v[4]) if v[4] else {}
    files_keys = list(meta.get("files", {}).keys())
    print(f"\n--- Version v{v_num} ({v_id}) status={v_status} ---")
    print(f"Files in metadata ({len(files_keys)}): {files_keys}")

    # Inspect App.tsx and index.html if present
    files_map = meta.get("files", {})
    if "frontend/index.html" in files_map:
        html = files_map["frontend/index.html"]
        print(f"index.html length: {len(html)}")
        print("index.html preview header/buttons:")
        for line in html.splitlines():
            if any(k in line.lower() for k in ["login", "btn-open-login", "auth-modal", "header", "<button"]):
                print("  HTML line:", line[:120])
    if "frontend/src/App.tsx" in files_map:
        app_tsx = files_map["frontend/src/App.tsx"]
        print(f"App.tsx length: {len(app_tsx)}")
        for line in app_tsx.splitlines():
            if any(k in line.lower() for k in ["login", "modal", "isloginopen"]):
                print("  App.tsx line:", line[:120])

conn.close()
