import asyncio, os, sys
sys.path.insert(0, os.path.abspath("backend"))
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as s:
        r = await s.execute(select(User.id, User.email, User.is_active).limit(5))
        users = r.all()
        for u in users:
            print("User:", u[0], u[1], u[2])

if __name__ == "__main__":
    asyncio.run(main())
