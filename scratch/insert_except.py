with open("backend/app/runtime/preview_server.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines[:200]):
    if "def sync_tasks_from_db():" in line:
        start_idx = idx
        break

print(f"sync_tasks_from_db starts at {start_idx+1}")
# Find conn.close() inside sync_tasks_from_db
for idx in range(start_idx, start_idx + 40):
    if "conn.close()" in lines[idx]:
        close_idx = idx
        break

print(f"conn.close() is at line {close_idx+1}: {repr(lines[close_idx])}")

# Insert the missing lines right after close_idx
insert_lines = [
    '        tasks_db = [{"id": r[0], "title": r[1], "description": r[2], "priority": r[3], "status": r[4], "due_date": r[5]} for r in rows]\n',
    '    except Exception:\n',
    '        pass\n',
    '    return tasks_db\n',
    '\n'
]

lines[close_idx+1:close_idx+1] = insert_lines

with open("backend/app/runtime/preview_server.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Successfully inserted missing except block for sync_tasks_from_db!")
