import sqlite3
import json
from pathlib import Path

db_path = Path("se_intelliplatform.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# Get column names of development_versions
cur.execute("PRAGMA table_info(development_versions)")
cols = [r[1] for r in cur.fetchall()]
print(f"development_versions columns: {cols}")

# Query the active version
cur.execute("SELECT * FROM development_versions WHERE id = ? OR id = ?", ("0093f7ff-4593-4e0a-916c-fbd8e6e16e4e", "0093f7ff45934e0a916cfbd8e6e16e4e"))
v_row = cur.fetchone()
if v_row:
    v_dict = dict(zip(cols, v_row))
    print("\n--- ACTIVE VERSION DETAILS ---")
    for k, v in v_dict.items():
        if k in ("files_manifest", "storage_reference") and v and len(str(v)) > 200:
            print(f"{k}: {str(v)[:200]}... (length: {len(str(v))})")
        else:
            print(f"{k}: {v}")

    # Inspect the manifest or version files
    if v_dict.get("files_manifest"):
        try:
            m = json.loads(v_dict["files_manifest"])
            print(f"\nManifest has {len(m)} files:")
            for item in m:
                path = item.get("path") or item.get("file_path") or item
                print(f"  - {path}")
        except Exception as e:
            print("Manifest parse err:", e)
else:
    print("Active version not found by ID")

# Check version_files table if exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%version%'")
print("\nTables with 'version':", cur.fetchall())

conn.close()
