from pathlib import Path

# 1. Update backend/app/api/v1/endpoints/preview_runtime.py
p1 = Path("backend/app/api/v1/endpoints/preview_runtime.py")
c1 = p1.read_text(encoding="utf-8")
old_block1 = """    if any(k in combined for k in ["student", "manage", "employee", "admin", "record", "faculty", "school"]):
        return "management"
    if any(k in combined for k in ["task", "todo", "action", "item", "flow", "kanban"]):
        return "taskflow\""""

new_block1 = """    if any(k in combined for k in ["task", "todo", "action", "item", "flow", "kanban"]):
        return "taskflow"
    if any(k in combined for k in ["student", "manage", "employee", "admin", "record", "faculty", "school"]):
        return "management\""""

if old_block1 in c1:
    c1 = c1.replace(old_block1, new_block1, 1)
    p1.write_text(c1, encoding="utf-8")
    print("SUCCESS: preview_runtime.py updated.")
else:
    c1_norm = c1.replace("\r\n", "\n")
    if old_block1 in c1_norm:
        c1_norm = c1_norm.replace(old_block1, new_block1, 1)
        p1.write_text(c1_norm, encoding="utf-8")
        print("SUCCESS: preview_runtime.py updated (norm).")
    else:
        print("ERROR: old_block1 not found.")

# 2. Update backend/app/runtime/preview_server.py
p2 = Path("backend/app/runtime/preview_server.py")
c2 = p2.read_text(encoding="utf-8")
old_block2 = """    if any(k in combined for k in ["student", "manage", "employee", "admin", "record", "faculty", "school"]):
        return "management"
    if any(k in combined for k in ["task", "todo", "action", "item", "flow", "kanban"]):
        return "taskflow\""""

new_block2 = """    if any(k in combined for k in ["task", "todo", "action", "item", "flow", "kanban"]):
        return "taskflow"
    if any(k in combined for k in ["student", "manage", "employee", "admin", "record", "faculty", "school"]):
        return "management\""""

if old_block2 in c2:
    c2 = c2.replace(old_block2, new_block2, 1)
    p2.write_text(c2, encoding="utf-8")
    print("SUCCESS: preview_server.py updated.")
else:
    c2_norm = c2.replace("\r\n", "\n")
    if old_block2 in c2_norm:
        c2_norm = c2_norm.replace(old_block2, new_block2, 1)
        p2.write_text(c2_norm, encoding="utf-8")
        print("SUCCESS: preview_server.py updated (norm).")
    else:
        print("ERROR: old_block2 not found.")

