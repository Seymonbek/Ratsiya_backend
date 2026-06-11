import io
import uuid
import wave

import pytest
from starlette.testclient import TestClient


def _wav_bytes(seconds: int = 5) -> bytes:
    """Test uchun haqiqiy WAV audio."""
    buf = io.BytesIO()
    rate = 8000
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(rate)
        w.writeframes(b"\x80" * (rate * seconds))
    return buf.getvalue()


@pytest.fixture
def sync_client():

    import asyncio

    from app.main import app
    from app.redis.client import RedisClient
    from app.db.session import engine

    # Oldingi async fixture ochgan ulanishlarni tozalash
    RedisClient._client = None
    # Engine pool'ini ham yangi loop'da tozalash (eski loop ulanishlari)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(engine.dispose())
    loop.close()

    with TestClient(app) as c:
        yield c


class TestWebSocket:
    """WebSocket testlari."""

    def test_ws_requires_valid_token(self, sync_client):
        """Yaroqsiz token bilan ulanish rad etilsin."""
        from starlette.websockets import WebSocketDisconnect
        with pytest.raises(WebSocketDisconnect):
            with sync_client.websocket_connect("/api/v1/ws?token=yaroqsiz"):
                pass

    def test_ws_ping_pong(self, sync_client):
        """Ulangan driver ping yuborsa, pong olsin."""
        # Driver yaratish
        username = f"dr_{uuid.uuid4().hex[:8]}"
        plate = f"{uuid.uuid4().hex[:6].upper()}"
        sync_client.post("/api/v1/auth/register/driver", json={
            "username": username, "password": "test123456",
            "full_name": "WS Driver", "license_plate": plate,
        })
        login = sync_client.post("/api/v1/auth/login", json={
            "username": username, "password": "test123456",
        })
        token = login.json()["access_token"]

        with sync_client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            ws.send_json({"event": "ping"})
            response = ws.receive_json()
            assert response["event"] == "pong"

    def test_ws_broadcast_autoplay(self, sync_client):
        """Operator broadcast yuborsa, ulangan online driver auto_play oladi."""
        # Operator
        op_username = f"op_{uuid.uuid4().hex[:8]}"
        sync_client.post("/api/v1/auth/register/operator", json={
            "username": op_username, "password": "test123456", "full_name": "Op",
        })
        op_token = sync_client.post("/api/v1/auth/login", json={
            "username": op_username, "password": "test123456",
        }).json()["access_token"]

        # Driver
        dr_username = f"dr_{uuid.uuid4().hex[:8]}"
        plate = f"{uuid.uuid4().hex[:6].upper()}"
        sync_client.post("/api/v1/auth/register/driver", json={
            "username": dr_username, "password": "test123456",
            "full_name": "Driver", "license_plate": plate,
        })
        dr_token = sync_client.post("/api/v1/auth/login", json={
            "username": dr_username, "password": "test123456",
        }).json()["access_token"]

        # Driver online
        sync_client.patch(
            "/api/v1/drivers/me/status",
            json={"status": "online"},
            headers={"Authorization": f"Bearer {dr_token}"},
        )

        # Driver WebSocket'ga ulanadi, keyin operator broadcast yuboradi
        with sync_client.websocket_connect(f"/api/v1/ws?token={dr_token}") as ws:
            files = {"file": ("t.wav", _wav_bytes(5), "audio/wav")}
            sync_client.post(
                "/api/v1/messages/broadcast",
                files=files,
                headers={"Authorization": f"Bearer {op_token}"},
            )
            # Real-time xabar kelishi kerak
            msg = ws.receive_json()
            assert msg["event"] == "new_voice_message"
            assert msg["auto_play"] is True
            assert "audio_url" in msg["data"]
