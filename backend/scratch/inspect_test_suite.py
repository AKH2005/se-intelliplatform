import asyncio
import selectors
import sys
import uuid
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# On Windows with psycopg, set SelectorEventLoop
loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
asyncio.set_event_loop(loop)

from app.db.session import async_session_factory
from app.agents.test_generation.service import AITestService

async def main():
    async with async_session_factory() as session:
        svc = AITestService(session)
        pid = uuid.UUID("df084c2c-4fff-464f-84a3-9104f07f31c4")
        suite_id = uuid.UUID("f2619bb5-a205-4923-b396-9e5c82a62655")
        suite = await svc.get_test_suite(pid, suite_id)
        print(f"Suite ID: {suite.suite_id}")
        print(f"Total tests: {len(suite.tests)}")
        print(f"Test files: {list(suite.test_files.keys())}")
        for k, v in suite.test_files.items():
            print(f"--- {k} ---")
            print(v)

if __name__ == "__main__":
    asyncio.run(main())
