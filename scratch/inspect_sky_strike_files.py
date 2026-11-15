import sqlite3
import json
from pathlib import Path

db_path = Path("se_intelliplatform.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# Query version metadata
cur.execute("SELECT metadata FROM development_versions WHERE id = ?", ("0093f7ff45934e0a916cfbd8e6e16e4e",))
row = cur.fetchone()
if row and row[0]:
    meta = json.loads(row[0])
    files = meta.get("files", {})
    print(f"Files in version: {list(files.keys())}")
    index_html = files.get("frontend/index.html", "")
    print(f"\nfrontend/index.html length: {len(index_html)}")
    print("Contains 'Shadow Master':", "Shadow Master" in index_html)
    print("Contains 'Sky Strike':", "Sky Strike" in index_html)
    print("Contains 'combatCanvas':", "combatCanvas" in index_html)
    print("Contains 'dogfight':", "dogfight" in index_html)
    print("Contains 'aerial':", "aerial" in index_html)

    # Print first 50 lines of index.html
    lines = index_html.splitlines()
    print("\n--- First 60 lines of frontend/index.html ---")
    for l in lines[:60]:
        print(l)

    # Search for keywords in index_html
    print("\n--- Title and Headers in index.html ---")
    for l in lines:
        if "<title>" in l or "<h1>" in l or "<h2>" in l or "class=\"badge\"" in l or "shadow" in l.lower():
            print("  ", l.strip()[:100])

conn.close()
