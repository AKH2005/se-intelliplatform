import asyncio
import urllib.request
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from sqlalchemy import select


async def test_rollback():
    transport = ASGITransport(app=app)
    async with AsyncSessionLocal() as session:
        proj_id = "eeae71c4-f4fa-4a6c-900b-8c65f6fe8b1b"
        res_u = await session.execute(select(User).limit(1))
        owner = res_u.scalar_one()
        token = create_access_token({"sub": str(owner.id)})

    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        list_res = await client.get(f"/api/v1/projects/{proj_id}/versions", headers=headers)
        versions = list_res.json()["items"]
        print(f"Total versions in project: {len(versions)}")
        target_v2 = [v for v in versions if v["version_number"] == 2][0]
        print(f"Targeting rollback to v2: id={target_v2['version_id']}")

        rb_res = await client.post(
            f"/api/v1/projects/{proj_id}/versions/{target_v2['version_id']}/rollback",
            headers=headers,
            json={"reason": "Live rollback verification from User Mode"},
        )
        assert rb_res.status_code == 200, f"Rollback failed: {rb_res.text}"
        print(f"Rollback status: 200 OK. Active version is now: v{rb_res.json().get('version_number')}")

    # Wait for container reload and file synchronization
    print("Waiting for container reload...")
    await asyncio.sleep(3.0)

    for i in range(10):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8001/", timeout=3) as r:
                body = r.read().decode("utf-8")
                print("Container HTTP Status:", r.status)
                print("Snippet:", body[:180])
                is_v2 = "Refined Dark Mode" not in body
                print(f"Reverted to baseline v2 (Refined Dark Mode removed)? {is_v2}")
                assert is_v2, "Expected container to reflect rolled back files"
                print("SUCCESS: 1-Click Rollback verified against real running Docker container!")
                return
        except Exception as e:
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(test_rollback())

