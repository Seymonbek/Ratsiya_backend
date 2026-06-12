import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.constants import WS_RECEIVE_TIMEOUT
from app.core.logger import setup_logger
from app.core.security import decode_access_token
from app.db.session import async_session_factory
from app.enums import DriverStatus, UserRole
from app.repositories.user import user_repository
from app.repositories.driver import driver_repository
from app.redis import presence
from app.redis import token_blacklist
from app.websocket.manager import ws_manager
from app.websocket.events import handle_event

logger = setup_logger(__name__)

router = APIRouter(tags=["WebSocket"])


async def _set_driver_status(user_id: int, status: DriverStatus) -> None:

    async with async_session_factory() as session:
        # Atomik yangilash (race condition'siz):
        #   - online qilish: faqat offline'dan
        #   - offline qilish: faqat online'dan
        #   - on_trip (band) — hech qachon o'zgartirilmaydi (expected'ga kirmaydi)
        if status == DriverStatus.ONLINE:
            expected = [DriverStatus.OFFLINE]
        elif status == DriverStatus.OFFLINE:
            expected = [DriverStatus.ONLINE]
        else:
            return

        changed = await driver_repository.update_status_atomic(
            session, user_id, status, expected
        )
        if changed:
            await session.commit()


async def _on_disconnect(user_id: int, websocket: WebSocket, is_driver: bool) -> None:

    was_last = ws_manager.disconnect(user_id, websocket)
    if is_driver and was_last:
        # Redis presence'ni darhol o'chirish (TTL kutmasdan)
        await presence.mark_offline(user_id)
        # DB statusini offline qilish (state desync oldini olish)
        await _set_driver_status(user_id, DriverStatus.OFFLINE)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):

    # 1. Tokenni tekshirish
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=1008, reason="Token yaroqsiz")
        return

    sub = payload.get("sub")
    if sub is None or not str(sub).isdigit():
        await websocket.close(code=1008, reason="Token yaroqsiz")
        return
    user_id = int(sub)

    # Token bekor qilinganmi (logout / revoked)
    if await token_blacklist.is_revoked(payload.get("jti", "")):
        await websocket.close(code=1008, reason="Token bekor qilingan")
        return

    # 2. Foydalanuvchini yuklash (ruxsat tekshiruvlari uchun kerak)
    async with async_session_factory() as session:
        user = await user_repository.get_by_id(session, user_id)
    if user is None or not user.is_active:
        await websocket.close(code=1008, reason="Foydalanuvchi topilmadi")
        return

    is_driver = user.role == UserRole.DRIVER

    # 3. Ulanishni qabul qilish
    await ws_manager.connect(websocket, user_id)

    # 4. Driver bo'lsa — online qilish (DB status + Redis presence)
    if is_driver:
        await _set_driver_status(user_id, DriverStatus.ONLINE)
        await presence.mark_online(user_id)

    try:
        while True:

            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=WS_RECEIVE_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.info(
                    f"WebSocket timeout (user_id={user_id}): "
                    f"{WS_RECEIVE_TIMEOUT}s sukunat, ulanish yopilmoqda"
                )
                await websocket.close(code=1001, reason="Heartbeat timeout")
                break
            except (ValueError, TypeError):
                await websocket.send_json({
                    "event": "error",
                    "data": {"message": "Noto'g'ri JSON format"},
                })
                continue

            event_type = data.get("event", "")

            # Har qanday xabar = "tirikman" signali → presence TTL yangilash
            if is_driver:
                await presence.mark_online(user_id)

            # Har bir event uchun yangi DB session
            async with async_session_factory() as session:
                response = await handle_event(event_type, data, session, user)
            await websocket.send_json(response)

    except WebSocketDisconnect:
        await _on_disconnect(user_id, websocket, is_driver)
        logger.info(f"WebSocket uzildi: user_id={user_id}")

    except Exception as e:
        logger.error(f"WebSocket xatosi (user_id={user_id}): {e}")
        await _on_disconnect(user_id, websocket, is_driver)
