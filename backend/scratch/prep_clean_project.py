import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as s:
        await s.execute(text("UPDATE projects SET slug = 'taskflow-prev', name = 'TaskFlow (Previous)' WHERE slug = 'taskflow'"))
        await s.commit()
        print("Updated old taskflow slug successfully.")

if __name__ == "__main__":
    asyncio.run(main())
