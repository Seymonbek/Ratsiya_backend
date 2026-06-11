import uuid

import pytest


class TestAuthFlow:
    """Autentifikatsiya oqimi."""

    @pytest.mark.asyncio
    async def test_register_and_login_operator(self, client):
        """Operator yaratish va login."""
        username = f"op_{uuid.uuid4().hex[:8]}"
        # Register
        r = await client.post("/api/v1/auth/register/operator", json={
            "username": username, "password": "test123456", "full_name": "Operator",
        })
        assert r.status_code == 201
        assert r.json()["role"] == "operator"

        # Login
        r = await client.post("/api/v1/auth/login", json={
            "username": username, "password": "test123456",
        })
        assert r.status_code == 200
        assert "access_token" in r.json()

    @pytest.mark.asyncio
    async def test_wrong_password_rejected(self, client):
        """Noto'g'ri parol 401 qaytarsin."""
        username = f"op_{uuid.uuid4().hex[:8]}"
        await client.post("/api/v1/auth/register/operator", json={
            "username": username, "password": "test123456", "full_name": "Op",
        })
        r = await client.post("/api/v1/auth/login", json={
            "username": username, "password": "notog'ri_parol",
        })
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_duplicate_username_rejected(self, client):
        """Takroriy username 409 qaytarsin."""
        username = f"op_{uuid.uuid4().hex[:8]}"
        data = {"username": username, "password": "test123456", "full_name": "Op"}
        await client.post("/api/v1/auth/register/operator", json=data)
        r = await client.post("/api/v1/auth/register/operator", json=data)
        assert r.status_code == 409


class TestDriverFlow:
    """Driver status oqimi."""

    @pytest.mark.asyncio
    async def test_driver_status_update(self, client):
        """Driver statusini online qiladi."""
        username = f"dr_{uuid.uuid4().hex[:8]}"
        plate = f"{uuid.uuid4().hex[:6].upper()}"
        await client.post("/api/v1/auth/register/driver", json={
            "username": username, "password": "test123456",
            "full_name": "Driver", "license_plate": plate,
        })
        login = await client.post("/api/v1/auth/login", json={
            "username": username, "password": "test123456",
        })
        token = login.json()["access_token"]

        r = await client.patch(
            "/api/v1/drivers/me/status",
            json={"status": "online"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "online"


class TestMessagePermissions:
    """Xabar ruxsatlari (TZ qoidalari)."""

    @pytest.mark.asyncio
    async def test_driver_cannot_send(self, client):
        """Driver xabar yubora olmaydi (403)."""
        username = f"dr_{uuid.uuid4().hex[:8]}"
        plate = f"{uuid.uuid4().hex[:6].upper()}"
        await client.post("/api/v1/auth/register/driver", json={
            "username": username, "password": "test123456",
            "full_name": "Driver", "license_plate": plate,
        })
        login = await client.post("/api/v1/auth/login", json={
            "username": username, "password": "test123456",
        })
        token = login.json()["access_token"]

        files = {"file": ("test.webm", b"audio data", "audio/webm")}
        r = await client.post(
            "/api/v1/messages/broadcast",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_can_broadcast(self, client, operator_token):
        """Operator broadcast yubora oladi va Redis'da saqlanadi."""
        files = {"file": ("test.webm", b"audio data here", "audio/webm")}
        r = await client.post(
            "/api/v1/messages/broadcast",
            files=files,
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["message_type"] == "broadcast"
        assert data["expires_in"] == 60

        # Audio Redis'dan olinishi mumkin
        audio_r = await client.get(
            data["audio_url"],
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert audio_r.status_code == 200
        assert audio_r.content == b"audio data here"

    @pytest.mark.asyncio
    async def test_private_to_offline_rejected(self, client, operator_token):
        """offline driverga private xabar 400 qaytarsin (TZ qoidasi)."""
        # Offline driver yaratish
        username = f"dr_{uuid.uuid4().hex[:8]}"
        plate = f"{uuid.uuid4().hex[:6].upper()}"
        reg = await client.post("/api/v1/auth/register/driver", json={
            "username": username, "password": "test123456",
            "full_name": "Offline Driver", "license_plate": plate,
        })
        # Driver default offline. Uning driver_id'sini olish uchun operator ro'yxatdan qidiramiz
        drivers = await client.get(
            "/api/v1/drivers",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        driver_id = next(
            d["id"] for d in drivers.json()["drivers"]
            if d["license_plate"] == plate
        )

        files = {"file": ("test.webm", b"audio", "audio/webm")}
        r = await client.post(
            f"/api/v1/messages/private/{driver_id}",
            files=files,
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert r.status_code == 400  # offline → rad etiladi
