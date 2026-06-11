import asyncio
import json

from app.core.logger import setup_logger
from app.redis.client import get_redis
from app.websocket.connections import connection_registry

logger = setup_logger(__name__)

# Pub/Sub kanal nomi — barcha serverlar shu kanalni tinglaydi
VOICE_CHANNEL = "ratsiya:voice"

# Subscriber task (server ishga tushganda boshlanadi)
_subscriber_task: asyncio.Task | None = None


async def publish_broadcast(payload: dict, online_user_ids: list[int]) -> None:

    redis_client = get_redis()
    message = json.dumps({
        "target": "broadcast",
        "user_ids": online_user_ids,
        "payload": payload,
    })
    n = await redis_client.publish(VOICE_CHANNEL, message)
    logger.debug(f"Broadcast publish: {len(online_user_ids)} user, servers={n}")


async def publish_to_user(user_id: int, payload: dict) -> None:

    redis_client = get_redis()
    message = json.dumps({
        "target": "user",
        "user_id": user_id,
        "payload": payload,
    })
    await redis_client.publish(VOICE_CHANNEL, message)


async def _handle_pubsub_message(data: dict) -> None:
   
    # Kech import (circular import'ni oldini olish)
    from app.websocket.manager import ws_manager

    target = data.get("target")
    payload = data.get("payload", {})

    if target == "broadcast":
        # Faqat shu serverga ulangan online driverlarga
        user_ids = data.get("user_ids", [])
        # Bu serverda ulangan bo'lganlarini filtrlash
        local_ids = [uid for uid in user_ids if connection_registry.is_connected(uid)]
        if local_ids:
            await ws_manager.send_to_many(local_ids, payload)

    elif target == "user":
        # Private — agar shu serverga ulangan bo'lsa
        user_id = data.get("user_id")
        if user_id is not None and connection_registry.is_connected(user_id):
            await ws_manager.send_to_user(user_id, payload)


async def _subscriber_loop() -> None:

    redis_client = get_redis()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(VOICE_CHANNEL)
    logger.info(f"Pub/Sub kanaliga obuna bo'lindi: {VOICE_CHANNEL}")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if message is None:
                continue
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                await _handle_pubsub_message(data)
            except Exception as e:
                logger.error(f"Pub/Sub xabarni qayta ishlashda xato: {e}", exc_info=True)
    except asyncio.CancelledError:
        # Server to'xtaganda
        await pubsub.unsubscribe(VOICE_CHANNEL)
        await pubsub.aclose()
        logger.info("Pub/Sub obunasi to'xtatildi")
        raise


async def start_subscriber() -> None:
    """Subscriber'ni ishga tushirish (lifespan startup)."""
    global _subscriber_task
    if _subscriber_task is None:
        _subscriber_task = asyncio.create_task(_subscriber_loop())
        logger.info("Pub/Sub subscriber ishga tushdi")


async def stop_subscriber() -> None:
    """Subscriber'ni to'xtatish (lifespan shutdown)."""
    global _subscriber_task
    if _subscriber_task is not None:
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass
        _subscriber_task = None
        logger.info("Pub/Sub subscriber to'xtatildi")
