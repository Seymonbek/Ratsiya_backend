import uuid

import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest_asyncio.fixture(scope="session")
async def client():

    from app.main import app
    from app.db.init_db import init_db
    from app.redis.client import RedisClient

    # Startup (bir marta)
    await init_db()
    await RedisClient.connect()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Shutdown (bir marta)
    await RedisClient.disconnect()


@pytest_asyncio.fixture
async def operator_token(client):
    """Operator yaratib, token qaytaradi (unikal username)."""
    username = f"op_{uuid.uuid4().hex[:8]}"
    await client.post("/api/v1/auth/register/operator", json={
        "username": username, "password": "test123456", "full_name": "Test Operator",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": username, "password": "test123456",
    })
    return resp.json()["access_token"]
