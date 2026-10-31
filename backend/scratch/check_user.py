import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal
from app.services.auth_service import AuthService
from app.schemas.auth import UserRegisterRequest, UserLoginRequest

async def main():
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session=session)
        user = await auth_service.get_by_email("capstone.dev@example.com")
        if user:
            print(f"User exists: {user.id}, {user.email}")
        else:
            print("User does not exist, creating test user...")
            req = UserRegisterRequest(
                email="capstone.dev@example.com",
                name="QA Capstone Dev",
                password="Password123!",
                confirm_password="Password123!"
            )
            u, token = await auth_service.register(req)
            print(f"Created user: {u.id}, {u.email}")
            
        # Test auth
        login_req = UserLoginRequest(email="capstone.dev@example.com", password="Password123!")
        u_auth, t = await auth_service.authenticate(login_req)
        print("Auth success! Token created.")

if __name__ == "__main__":
    asyncio.run(main())
