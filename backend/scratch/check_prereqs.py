import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text
from app.core.config import settings

async def main():
    db_type = settings.DATABASE_URL.split("://")[0]
    print(f"Database Driver: {db_type}")
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT count(*) FROM users;"))
        user_count = res.scalar()
        print(f"Database Connectivity: OK (User count: {user_count})")
        
        proj_res = await session.execute(text("SELECT count(*) FROM projects;"))
        proj_count = proj_res.scalar()
        print(f"Projects in Database: {proj_count}")
        
        # Check active AI providers
        groq_ok = bool(settings.GROQ_API_KEY)
        gemini_ok = bool(settings.GEMINI_API_KEY)
        print(f"AI Provider Groq: {'Configured' if groq_ok else 'Not Configured'}")
        print(f"AI Provider Gemini: {'Configured' if gemini_ok else 'Not Configured'}")

if __name__ == "__main__":
    asyncio.run(main())
