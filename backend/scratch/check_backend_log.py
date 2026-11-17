import re

with open(r'C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\.system_generated\tasks\task-17378.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Total lines in backend log: {len(lines)}")
for i, line in enumerate(lines):
    if "ADD_LOGIN_PAGE" in line or "restart_runtime" in line or "Changes were reverted" in line or "Could not refresh" in line:
        print(f"Line {i}: {line.strip()[:140]}")
        for j in range(max(0, i-5), min(len(lines), i+15)):
            if lines[j].strip() and "PRAGMA" not in lines[j] and "SELECT users" not in lines[j]:
                print(f"   [{j}] {lines[j].strip()[:140]}")
        print("---")
