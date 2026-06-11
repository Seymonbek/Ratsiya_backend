from fastapi import WebSocket

from app.core.logger import setup_logger

logger = setup_logger(__name__)


class ConnectionRegistry:
    def __init__(self) -> None:
        # user_id → WebSocket
        self._connections: dict[int, WebSocket] = {}

    def add(self, user_id: int, websocket: WebSocket) -> None:

        self._connections[user_id] = websocket
        logger.info(f"WebSocket ulandi: user_id={user_id} (jami: {len(self._connections)})")

    def remove(self, user_id: int) -> None:
        """Ulanishni o'chirish (driver uzilganda)."""
        if user_id in self._connections:
            del self._connections[user_id]
            logger.info(
                f"WebSocket uzildi: user_id={user_id} (qoldi: {len(self._connections)})"
            )

    def get(self, user_id: int) -> WebSocket | None:
        """Bitta user'ning ulanishini olish."""
        return self._connections.get(user_id)

    def is_connected(self, user_id: int) -> bool:
        """User ulanganmi tekshirish."""
        return user_id in self._connections

    def get_all_user_ids(self) -> list[int]:
        """Barcha ulangan user_id'lar."""
        return list(self._connections.keys())

    @property
    def active_count(self) -> int:
        """Aktiv ulanishlar soni."""
        return len(self._connections)


# Global registry — butun ilovada bitta (Singleton)
connection_registry = ConnectionRegistry()
