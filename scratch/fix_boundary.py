from pathlib import Path

p = Path("backend/app/runtime/preview_server.py")
content = p.read_text(encoding="utf-8")

bad_target = """        conn.close()
        
# ==============================================================================
# MEDIUM-COMPLEXITY SQLITE PERSISTENCE ENGINES & APIS"""

good_replacement = """        conn.close()
        tasks_db = [{"id": r[0], "title": r[1], "description": r[2], "priority": r[3], "status": r[4], "due_date": r[5]} for r in rows]
    except Exception:
        pass
    return tasks_db

# ==============================================================================
# MEDIUM-COMPLEXITY SQLITE PERSISTENCE ENGINES & APIS"""

if bad_target in content:
    content = content.replace(bad_target, good_replacement, 1)
    p.write_text(content, encoding="utf-8")
    print("Fixed boundary in preview_server.py")
else:
    print("bad_target not found")
