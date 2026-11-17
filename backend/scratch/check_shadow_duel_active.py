import asyncio
import sys
import uuid
backend_dir = r"c:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import AsyncSessionLocal
from app.services.development_version_service import DevelopmentVersionService

async def main():
    async with AsyncSessionLocal() as session:
        service = DevelopmentVersionService(session)
        pid = uuid.UUID("68289eab-12f4-4602-a4b7-143f29c52c58")
        active = await service.get_active_version(pid)
        print("Active version for Shadow Duel:", active)
        if active:
            print("Version number:", active.version_number)
            print("Status:", active.status)

asyncio.run(main())
