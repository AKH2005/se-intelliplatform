import urllib.request

pid = "68289eab-12f4-4602-a4b7-143f29c52c58"
url = f"http://127.0.0.1:8001/preview?project_id={pid}"
req = urllib.request.urlopen(url)
content = req.read().decode('utf-8')

print("Total length:", len(content))
for term in ["btn-open-login", "auth-modal-overlay", "auth-card", "pwd-meter", "link-forgot-password", "media (max-width"]:
    print(f"Contains '{term}':", term in content)

# Find where auth elements are
for line in content.splitlines():
    if "auth" in line.lower() or "login" in line.lower() or "password" in line.lower():
        print("  Line:", line[:120])
