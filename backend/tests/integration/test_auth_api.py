"""Integration Tests for Authentication System and Project Ownership Authorization."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_full_lifecycle(client: AsyncClient):
    """Test full registration, login, profile retrieval, and logout lifecycle."""
    # 1. Successful Registration
    reg_payload = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "password": "Password123",
        "confirm_password": "Password123",
    }
    res_reg = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201, res_reg.text
    data_reg = res_reg.json()
    assert "access_token" in data_reg
    assert data_reg["token_type"] == "bearer"
    assert data_reg["user"]["email"] == "jane@example.com"
    assert data_reg["user"]["name"] == "Jane Developer"

    token = data_reg["access_token"]

    # 2. Duplicate Registration Rejection
    res_dup = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res_dup.status_code in (400, 409)

    # 3. Successful Login
    login_payload = {
        "email": "jane@example.com",
        "password": "Password123",
    }
    res_login = await client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    data_login = res_login.json()
    assert "access_token" in data_login
    login_token = data_login["access_token"]

    # 4. Invalid Password Login
    bad_login = {
        "email": "jane@example.com",
        "password": "WrongPassword999",
    }
    res_bad = await client.post("/api/v1/auth/login", json=bad_login)
    assert res_bad.status_code == 401

    # 5. Invalid Email Format
    invalid_email = {
        "name": "Bad",
        "email": "not-an-email",
        "password": "Password123",
        "confirm_password": "Password123",
    }
    res_inv = await client.post("/api/v1/auth/register", json=invalid_email)
    assert res_inv.status_code == 422

    # 6. Protected Route Access (/me) with Token
    res_me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_token}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "jane@example.com"

    # 7. Protected Route without Token
    res_unauth = await client.get("/api/v1/auth/me")
    assert res_unauth.status_code == 401

    # 8. Protected Route with Invalid Token
    res_invalid_tok = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.garbage.token"},
    )
    assert res_invalid_tok.status_code == 401

    # 9. Logout
    res_logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_token}"},
    )
    assert res_logout.status_code == 200
    assert res_logout.json()["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_project_ownership_isolation(client: AsyncClient):
    """Verify that User A cannot access or modify projects owned by User B."""
    # Register User A
    user_a_res = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Alpha",
            "email": "alpha@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    assert user_a_res.status_code == 201
    token_a = user_a_res.json()["access_token"]

    # Register User B
    user_b_res = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Beta",
            "email": "beta@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    assert user_b_res.status_code == 201
    token_b = user_b_res.json()["access_token"]

    # User A creates a project
    proj_res = await client.post(
        "/api/v1/projects",
        json={
            "name": "Alpha Private Project",
            "slug": "alpha-private-proj",
            "description": "Confidential to Alpha",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert proj_res.status_code == 201, proj_res.text
    project_id = proj_res.json()["id"]

    # User A can access their project
    get_res_a = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_res_a.status_code == 200

    # User B is FORBIDDEN from accessing User A's project
    get_res_b = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res_b.status_code == 403

    # User B is FORBIDDEN from modifying User A's project
    patch_res_b = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Hacked Name"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert patch_res_b.status_code == 403

    # Unauthenticated user is FORBIDDEN from accessing User A's owned project
    get_unauth = await client.get(f"/api/v1/projects/{project_id}")
    assert get_unauth.status_code == 403
