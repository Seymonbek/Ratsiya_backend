from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.logger import setup_logger
from app.core.security import decode_access_token
from app.db.session import async_session_factory
from app.enums import DriverStatus, UserRole
from app.repositories.user import user_repository
from app.repositories.driver import driver_repository
from app.websocket.manager import ws_manager
from app.websocket.events import handle_event

logger = setup_logger(__name__)

router = APIRouter(tags=["WebSocket"])


async def _set_driver_status(user_id: int, status: DriverStatus) -> None:

    async with async_session_factory() as session:
        driver = await driver_repository.get_by_user_id(session, user_id)
        if driver is None:
            return

        # on_trip — zakas bilan band, ulanish holati uni o'zgartirmaydi
        if driver.status == DriverStatus.ON_TRIP:
            return

        # online qilish: faqat offline'dan
        if status == DriverStatus.ONLINE and driver.status == DriverStatus.OFFLINE:
            await driver_repository.update_status(session, driver, DriverStatus.ONLINE)
            await session.commit()
        # offline qilish: faqat online'dan
        elif status == DriverStatus.OFFLINE and driver.status == DriverStatus.ONLINE:
            await driver_repository.update_status(session, driver, DriverStatus.OFFLINE)
            await session.commit()


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

    # 2. Foydalanuvchini yuklash (ruxsat tekshiruvlari uchun kerak)
    async with async_session_factory() as session:
        user = await user_repository.get_by_id(session, user_id)
    if user is None or not user.is_active:
        await websocket.close(code=1008, reason="Foydalanuvchi topilmadi")
        return

    # 3. Ulanishni qabul qilish
    await ws_manager.connect(websocket, user_id)

    # 4. Driver bo'lsa — statusini "online" qilish (DB sinxron)
    if user.role == UserRole.DRIVER:
        await _set_driver_status(user_id, DriverStatus.ONLINE)

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except (ValueError, TypeError):
                await websocket.send_json({
                    "event": "error",
                    "data": {"message": "Noto'g'ri JSON format"},
                })
                continue

            event_type = data.get("event", "")
            # Har bir event uchun yangi DB session
            async with async_session_factory() as session:
                response = await handle_event(event_type, data, session, user)
            await websocket.send_json(response)

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        # Driver uzildi — statusni "offline" qilish (state desync oldini olish)
        if user.role == UserRole.DRIVER:
            await _set_driver_status(user_id, DriverStatus.OFFLINE)
        logger.info(f"WebSocket uzildi: user_id={user_id}")

    except Exception as e:
        logger.error(f"WebSocket xatosi (user_id={user_id}): {e}")
        ws_manager.disconnect(user_id)
        if user.role == UserRole.DRIVER:
            await _set_driver_status(user_id, DriverStatus.OFFLINE)
