import urllib.request

url = "http://127.0.0.1:8001/?project_id=51458fe8-776f-4325-9e5a-bfc33dce112d"
html = urllib.request.urlopen(url).read().decode("utf-8", errors="replace")
print("Length:", len(html))
print("Title:", html[html.find("<title>"):html.find("</title>")+8])
print("Contains 'Executive':", "Executive" in html)
print("Contains 'Revenue':", "Revenue" in html)
print("Contains 'Analytics':", "Analytics" in html)
print("Snippet:", html[100:600])
