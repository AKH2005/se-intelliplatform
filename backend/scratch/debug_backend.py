import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
print("Starting backend via uvicorn directly...")
try:
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")
except Exception as e:
    print("Direct start exception:", type(e), e)

