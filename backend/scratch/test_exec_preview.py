import httpx

PID = "d8dc8495-6b8a-4fe3-940a-2b436d475454"
r = httpx.get(f"http://127.0.0.1:8001/preview?project_id={PID}")
print("Status:", r.status_code)
html = r.text
print("Length:", len(html))
print("Has btn-open-login:", "btn-open-login" in html)
print("Has auth-modal-overlay:", "auth-modal-overlay" in html)

# Let's inspect where btn-open-login is placed
for line in html.splitlines():
    if "btn-open-login" in line:
        print("btn-open-login line:", line)
    if "auth-modal-overlay" in line:
        print("auth-modal-overlay line:", line)
