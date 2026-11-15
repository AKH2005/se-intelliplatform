import urllib.request, json

endpoints = [
    ("GET /api/inventory/products", "http://127.0.0.1:8001/api/inventory/products"),
    ("GET /api/inventory/stats", "http://127.0.0.1:8001/api/inventory/stats"),
    ("GET /api/lms/courses", "http://127.0.0.1:8001/api/lms/courses"),
    ("GET /api/lms/progress", "http://127.0.0.1:8001/api/lms/progress"),
    ("GET /api/events", "http://127.0.0.1:8001/api/events"),
    ("GET /api/registrations", "http://127.0.0.1:8001/api/registrations"),
    ("GET /api/ecommerce/products", "http://127.0.0.1:8001/api/ecommerce/products"),
    ("GET /inventory HTML", "http://127.0.0.1:8001/inventory"),
    ("GET /lms HTML", "http://127.0.0.1:8001/lms"),
    ("GET /eventhub HTML", "http://127.0.0.1:8001/eventhub"),
    ("GET /ecommerce HTML", "http://127.0.0.1:8001/ecommerce"),
    ("GET /sky_strike HTML", "http://127.0.0.1:8001/sky_strike"),
]

for label, url in endpoints:
    try:
        res = urllib.request.urlopen(url)
        content_type = res.headers.get("content-type", "")
        data = res.read()
        print(f"[HTTP {res.status}] {label} (bytes: {len(data)}, type: {content_type.split(';')[0]})")
    except Exception as e:
        print(f"[FAILED] {label}: {e}")
