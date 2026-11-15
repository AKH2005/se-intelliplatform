from pathlib import Path

p = Path("backend/app/runtime/preview_server.py")
content = p.read_text(encoding="utf-8")

bad_snippet = """tasks_db = [{"id": r[0], "title": r[1], "description": r[2], "priority": r[3], "status": r[4], "due_date": r[5]} for r in rows]
    except Exception:
        pass
    return tasks_db"""

if bad_snippet in content:
    content = content.replace(bad_snippet, "", 1)
    p.write_text(content, encoding="utf-8")
    print("Cleaned up orphaned block successfully.")
else:
    print("bad_snippet not found")
