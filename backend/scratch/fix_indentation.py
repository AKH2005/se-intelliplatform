from pathlib import Path

target_file = Path("backend/app/runtime/preview_runtime_manager.py")
lines = target_file.read_text(encoding="utf-8").splitlines(keepends=True)

# Find where _ensure_running_unlocked starts
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "async def _ensure_running_unlocked(" in line:
        start_idx = i
    if start_idx is not None and "async def restart_runtime(" in line:
        end_idx = i
        break

assert start_idx is not None and end_idx is not None, f"Indices not found: {start_idx}, {end_idx}"

# Let's inspect the target lines
sub = lines[start_idx:end_idx]

# Line by line inspection:
# Lines up to 'if not force_restart:' (and its return) stay as is.
# From '# 2. If project_id is provided' down to the end of the method should be unindented by 4 spaces.

new_sub = []
unindent = False
for line in sub:
    if "# 2. If project_id is provided" in line:
        unindent = True
    if unindent:
        if line.startswith("    "):
            new_sub.append(line[4:])
        else:
            new_sub.append(line)
    else:
        new_sub.append(line)

lines[start_idx:end_idx] = new_sub
target_file.write_text("".join(lines), encoding="utf-8")
print("SUCCESSFULLY UNINDENTED _ensure_running_unlocked")

