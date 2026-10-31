import sqlite3
import json
from pathlib import Path

DB_PATH = Path("backend/se_intelliplatform.db")

def test_dark_mode(target_pid):
    print("Testing dark mode for PID:", target_pid)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    pid_str = str(target_pid)
    pid_hex = pid_str.replace("-", "")
    cur.execute("SELECT id, settings FROM projects WHERE id = ? OR id = ?", (pid_str, pid_hex))
    row = cur.fetchone()
    print("Project row:", row)
    if row and row[1]:
        settings_dict = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        print("Settings dict:", settings_dict)
        active_vid = settings_dict.get("active_version_id")
        print("active_vid:", active_vid)
        if active_vid:
            vid_str = str(active_vid)
            vid_hex = vid_str.replace("-", "")
            cur.execute("SELECT id, version_number FROM development_versions WHERE id = ? OR id = ?", (vid_str, vid_hex))
            v_row = cur.fetchone()
            print("Version row:", v_row)
            if v_row and v_row[1] is not None:
                v_num = int(v_row[1])
                print("v_num:", v_num)
                print("is_dark_mode_active ->", v_num > 1)
                return v_num > 1
    conn.close()
    return False

if __name__ == "__main__":
    test_dark_mode("b7312ca0-9967-4c0e-8e71-20276ce581ca")

