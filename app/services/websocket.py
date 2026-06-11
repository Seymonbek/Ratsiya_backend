from app.core.logger import setup_logger
from app.schemas.message import CachedVoiceMessage
from app.utils.helpers import build_audio_url
from app.redis.pubsub import publish_broadcast, publish_to_user

logger = setup_logger(__name__)


class WebSocketService:
    """Real-time xabar yetkazish servisi (Pub/Sub orqali)."""

    @staticmethod
    def _build_payload(meta: CachedVoiceMessage) -> dict:

        return {
            "event": "new_voice_message",
            "auto_play": True,
            "data": {
                "message_id": meta.message_id,
                "sender_name": meta.sender_name,
                "message_type": meta.message_type,
                "audio_url": build_audio_url(meta.message_id),
                "timestamp": meta.created_at,
            },
        }

    @staticmethod
    async def deliver_broadcast(
        online_user_ids: list[int],
        meta: CachedVoiceMessage,
    ) -> int:

        payload = WebSocketService._build_payload(meta)
        await publish_broadcast(payload, online_user_ids)
        return len(online_user_ids)

    @staticmethod
    async def deliver_private(
        driver_user_id: int,
        meta: CachedVoiceMessage,
    ) -> bool:

        payload = WebSocketService._build_payload(meta)
        await publish_to_user(driver_user_id, payload)
        return True


websocket_service = WebSocketService()
