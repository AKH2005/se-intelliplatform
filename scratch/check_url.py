import urllib.request

url = "http://127.0.0.1:8001/?project_id=51458fe8-776f-4325-9e5a-bfc33dce112d"
with urllib.request.urlopen(url) as resp:
    text = resp.read().decode("utf-8")
    print(f"Status: {resp.status}")
    print(f"Length: {len(text)}")
    t_start = text.find("<title>")
    t_end = text.find("</title>")
    if t_start != -1 and t_end != -1:
        print("Title:", text[t_start+7:t_end])
    matching_lines = [l.strip() for l in text.splitlines() if "new-task-input" in l]
    print(f"Lines containing new-task-input ({len(matching_lines)}):")
    for l in matching_lines[:5]:
        print("  ", l)

