import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.project import Project
from app.core.security import create_access_token


async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User))
        users = res.scalars().all()
        print(f"Users found ({len(users)}):")
        for u in users:
            print(f"  ID: {u.id}, Email: {u.email}, Active: {u.is_active}")

        res_p = await session.execute(select(Project))
        projects = res_p.scalars().all()
        print(f"\nProjects found ({len(projects)}):")
        for p in projects:
            print(f"  ID: {p.id}, Name: {p.name}, Owner: {p.owner_id}")

        if users:
            token = create_access_token(str(users[0].id))
            print(f"\nValid Token for {users[0].email}: (length: {len(token)})")


if __name__ == "__main__":
    asyncio.run(main())
