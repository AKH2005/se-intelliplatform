import sys, os
sys.path.insert(0, os.path.abspath("backend"))
from app.runtime.preview_server import get_custom_interactive_html
html = get_custom_interactive_html("Quantum Inventory Hub", "Warehouse inventory tracking")
print("Length:", len(html))
print("Start:", html[:300])
with open("scratch/universal_out.html", "w", encoding="utf-8") as f:
    f.write(html)

