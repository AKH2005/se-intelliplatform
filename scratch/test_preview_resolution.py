import urllib.request

projects = [
    ("EventHub", "903c7fa7-bb40-4258-b8a5-71df66251e5d", "EventHub"),
    ("Inventory", "857dbc09-b6ec-4784-9a60-b8dde5b14098", "Apex Inventory"),
    ("LMS", "29287b5a-ba89-4e50-9b3a-fb8b265a1f41", "SkillForge"),
    ("E-Commerce", "20b3db24-24c0-4949-8965-f41e61d4e5cb", "CyberMart"),
    ("Sky Strike", "b24ed9b4-6589-4b4b-b402-a1c08a399fb1", "Sky Strike"),
]

for label, pid, expected_text in projects:
    url = f"http://127.0.0.1:8001/preview/{pid}"
    try:
        res = urllib.request.urlopen(url)
        content = res.read().decode('utf-8')
        has_text = expected_text in content
        print(f"[{'PASS' if has_text else 'FAIL'}] {label} (PID: {pid[:8]}...): status {res.status}, contains '{expected_text}': {has_text}, len: {len(content)}")
    except Exception as e:
        print(f"[ERROR] {label}: {e}")
