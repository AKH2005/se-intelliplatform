with open("backend/app/runtime/preview_server.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for idx, line in enumerate(lines):
    if idx in range(632, 636):
        continue
    new_lines.append(line)

with open("backend/app/runtime/preview_server.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Removed lines 633-636 successfully!")
