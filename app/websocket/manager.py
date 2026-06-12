import asyncio

from fastapi import WebSocket

from app.core.logger import setup_logger
from app.websocket.connections import connection_registry

logger = setup_logger(__name__)

BROADCAST_BATCH_SIZE = 500


class WebSocketManager:
    """WebSocket ulanishlar menejeri."""

    @staticmethod
    async def connect(websocket: WebSocket, user_id: int) -> None:
        """Yangi ulanishni qabul qilish."""
        await websocket.accept()
        connection_registry.add(user_id, websocket)

    @staticmethod
    def disconnect(user_id: int, websocket: WebSocket) -> bool:

        return connection_registry.remove(user_id, websocket)

    @staticmethod
    async def send_to_user(user_id: int, data: dict) -> bool:

        sockets = connection_registry.get(user_id)
        if not sockets:
            return False

        sent_any = False
        # set ustida iteratsiya paytida o'zgartirmaslik uchun nusxa
        for websocket in list(sockets):
            try:
                await websocket.send_json(data)
                sent_any = True
            except Exception as e:
                # Ulanish buzilgan — registry'dan o'chiramiz (memory leak yo'q)
                logger.warning(f"User {user_id} ga yuborishda xato: {e}")
                connection_registry.remove(user_id, websocket)

        return sent_any

    @staticmethod
    async def send_to_many(user_ids: list[int], data: dict) -> int:

        if not user_ids:
            return 0

        sent_count = 0

        # Batch'lab yuborish (500 talik bo'laklar)
        for i in range(0, len(user_ids), BROADCAST_BATCH_SIZE):
            batch = user_ids[i:i + BROADCAST_BATCH_SIZE]

            # Bu batch'dagi hammaga BIR VAQTDA yuborish
            results = await asyncio.gather(
                *[WebSocketManager.send_to_user(uid, data) for uid in batch],
                return_exceptions=True,  # bitta xato boshqalarni to'xtatmasin
            )

            # Muvaffaqiyatlilarni sanash
            sent_count += sum(1 for r in results if r is True)

        logger.info(f"Broadcast: {sent_count}/{len(user_ids)} driverga yuborildi")
        return sent_count


ws_manager = WebSocketManager()
