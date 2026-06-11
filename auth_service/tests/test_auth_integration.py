import pytest
from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"email": "surname@email.com", "password": "testpass123"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"email": "duplicate@email.com", "password": "testpass123"}

        resp1 = await client.post("/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = await client.post("/auth/register", json=payload)
        assert resp2.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "testpass123"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={"email": "login@email.com", "password": "testpass123"},
        )

        resp = await client.post(
            "/auth/login",
            data={"username": "login@email.com", "password": "testpass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={"email": "wrongpass@email.com", "password": "testpass123"},
        )

        resp = await client.post(
            "/auth/login",
            data={"username": "wrongpass@email.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/auth/login",
            data={"username": "nouser@email.com", "password": "testpass123"},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_success(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"email": "me@email.com", "password": "testpass123"},
        )
        token = resp.json()["access_token"]

        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@email.com"
        assert data["role"] == "user"
        assert "id" in data
        assert "created_at" in data

    async def test_me_no_token(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    async def test_me_expired_token(self, client: AsyncClient):
        from datetime import timedelta

        from app.core.security import create_access_token

        token = create_access_token(
            sub="999",
            role="user",
            expires_delta=timedelta(seconds=-1),
        )

        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


class TestFullFlow:
    async def test_register_login_me_flow(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"email": "fullflow@email.com", "password": "securepass"},
        )
        assert resp.status_code == 201

        resp = await client.post(
            "/auth/login",
            data={"username": "fullflow@email.com", "password": "securepass"},
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "fullflow@email.com"
        assert data["role"] == "user"
