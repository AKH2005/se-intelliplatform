import sys
print("Python version:", sys.version)

try:
    from app.services.application_developer_service import ApplicationDeveloperService
    print("ApplicationDeveloperService imported successfully!")
except Exception as e:
    print("Error importing ApplicationDeveloperService:", e)
    raise

try:
    from app.api.v1.endpoints import assistant
    print("app.api.v1.endpoints.assistant imported successfully!")
except Exception as e:
    print("Error importing assistant endpoint:", e)
    raise

try:
    from app.main import app
    print("FastAPI app imported successfully!")
except Exception as e:
    print("Error importing app.main:", e)
    raise
