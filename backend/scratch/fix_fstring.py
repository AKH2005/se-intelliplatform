from pathlib import Path

p = Path("backend/scratch/qa_senior_e2e_test.py")
lines = p.read_text(encoding="utf-8").splitlines()

new_lines = []
for i, line in enumerate(lines):
    if 'log(f"Backend startup log:' in line:
        new_lines.append('                content_log = f.read()[:1000]')
        new_lines.append('                log(f"Backend startup log: {content_log}")')
    elif '{f.read()[:1000]}' in line:
        continue
    else:
        new_lines.append(line)

p.write_text("\n".join(new_lines), encoding="utf-8")
print("Fixed lines successfully.")

