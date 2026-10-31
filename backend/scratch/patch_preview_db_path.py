from pathlib import Path

path = Path(__file__).resolve().parent.parent / "app" / "runtime" / "preview_server.py"
text = path.read_text(encoding="utf-8")
if "DB_PATH = " not in text:
    target = "import sys\n"
    replacement = "import sys\nfrom pathlib import Path\nDB_PATH = Path(__file__).resolve().parent.parent.parent / 'se_intelliplatform.db'\n"
    text = text.replace(target, replacement, 1)
    text = text.replace('sqlite3.connect("se_intelliplatform.db")', 'sqlite3.connect(str(DB_PATH))')
    path.write_text(text, encoding="utf-8")
    print("SUCCESS: patched preview_server.py")
else:
    print("ALREADY PATCHED")

