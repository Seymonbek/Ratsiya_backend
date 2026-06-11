from app.core.logger import setup_logger
from app.redis.cache import get_voice_meta, get_voice_ttl
from app.utils.helpers import build_audio_url

logger = setup_logger(__name__)


async def handle_event(event_type: str, data: dict) -> dict:
    """Driver'dan kelgan event'ni qayta ishlash."""
    if event_type == "ping":
        return {"event": "pong"}

    if event_type == "replay":
        return await _handle_replay(data)

    return {
        "event": "error",
        "data": {"message": f"Noma'lum event: {event_type}"},
    }


async def _handle_replay(data: dict) -> dict:

    message_id = data.get("message_id")
    if message_id is None:
        return {"event": "error", "data": {"message": "message_id kerak"}}

    meta = await get_voice_meta(message_id)
    if meta is None:
        # 60s o'tgan — o'chib ketgan
        return {
            "event": "replay_expired",
            "data": {
                "message_id": message_id,
                "message": "Xabar muddati o'tgan (60 soniyadan ko'p)",
            },
        }

    ttl = await get_voice_ttl(message_id)
    return {
        "event": "replay_message",
        "auto_play": True,
        "data": {
            "message_id": meta.message_id,
            "sender_name": meta.sender_name,
            "message_type": meta.message_type,
            "audio_url": build_audio_url(meta.message_id),
            "timestamp": meta.created_at,
            "seconds_remaining": ttl,
        },
    }
