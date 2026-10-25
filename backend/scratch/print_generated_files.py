import asyncio
import selectors
import sys
import uuid
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
asyncio.set_event_loop(loop)

from app.core.database import AsyncSessionLocal
from app.runtime.application_runtime_manager import ApplicationRuntimeManager

async def main():
    async with AsyncSessionLocal() as session:
        mgr = ApplicationRuntimeManager(session=session)
        pid = uuid.UUID("df084c2c-4fff-464f-84a3-9104f07f31c4")
        vid = uuid.UUID("1d38bf10-0f3f-4160-9692-37c04c24c6a8")
        files_map, manifest = await mgr.resolve_version_files_and_manifest(project_id=pid, version_id=vid)
        print("Manifest:", manifest)
        print("Files:")
        for path, content in files_map.items():
            print(f"=== {path} ===")
            print(content)

if __name__ == "__main__":
    loop.run_until_complete(main())
