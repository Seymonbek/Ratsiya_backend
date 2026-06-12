from fastapi import WebSocket

from app.core.logger import setup_logger

logger = setup_logger(__name__)


class ConnectionRegistry:

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}

    def add(self, user_id: int, websocket: WebSocket) -> None:
        """Yangi ulanish qo'shish (mavjud ulanishlarga qo'shiladi)."""
        self._connections.setdefault(user_id, set()).add(websocket)
        logger.info(
            f"WebSocket ulandi: user_id={user_id} "
            f"(bu user: {len(self._connections[user_id])}, "
            f"jami user: {len(self._connections)})"
        )

    def remove(self, user_id: int, websocket: WebSocket) -> bool:

        sockets = self._connections.get(user_id)
        if sockets is None:
            return False

        sockets.discard(websocket)
        if not sockets:
            del self._connections[user_id]
            logger.info(
                f"WebSocket uzildi: user_id={user_id} (oxirgi ulanish, "
                f"qoldi: {len(self._connections)} user)"
            )
            return True

        logger.info(
            f"WebSocket uzildi: user_id={user_id} "
            f"(bu user: {len(sockets)} ulanish qoldi)"
        )
        return False

    def get(self, user_id: int) -> set[WebSocket]:
        """User'ning barcha ulanishlari (bo'sh set bo'lishi mumkin)."""
        return self._connections.get(user_id, set())

    def is_connected(self, user_id: int) -> bool:
        """User'ning kamida bitta ulanishi bormi."""
        return user_id in self._connections

    def get_all_user_ids(self) -> list[int]:
        """Barcha ulangan user_id'lar."""
        return list(self._connections.keys())

    @property
    def active_count(self) -> int:
        """Aktiv ulanishlar soni (barcha socketlar, hamma user bo'yicha)."""
        return sum(len(s) for s in self._connections.values())


connection_registry = ConnectionRegistry()
