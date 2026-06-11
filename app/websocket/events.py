from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import setup_logger
from app.models.user import User
from app.redis.cache import get_voice_meta, get_voice_ttl
from app.utils.helpers import build_audio_url

logger = setup_logger(__name__)


async def handle_event(
    event_type: str,
    data: dict,
    db: AsyncSession,
    user: User,
) -> dict:

    if event_type == "ping":
        return {"event": "pong"}

    if event_type == "replay":
        return await _handle_replay(data, db, user)

    return {
        "event": "error",
        "data": {"message": f"Noma'lum event: {event_type}"},
    }


async def _handle_replay(data: dict, db: AsyncSession, user: User) -> dict:

    message_id = data.get("message_id")
    if message_id is None:
        return {"event": "error", "data": {"message": "message_id kerak"}}

    meta = await get_voice_meta(message_id)
    if meta is None:
        return {
            "event": "replay_expired",
            "data": {
                "message_id": message_id,
                "message": "Xabar muddati o'tgan (60 soniyadan ko'p)",
            },
        }

    # Ruxsat tekshirish (private xabar maxfiyligi)
    from app.services.message import message_service

    if not await message_service.can_user_access(db, user, meta):
        return {
            "event": "error",
            "data": {"message": "Bu xabarni eshitishga ruxsatingiz yo'q"},
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
