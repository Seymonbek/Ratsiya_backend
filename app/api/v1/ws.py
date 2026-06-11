from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.logger import setup_logger
from app.core.security import decode_access_token
from app.websocket.manager import ws_manager
from app.websocket.events import handle_event

logger = setup_logger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):

    # 1. Tokenni tekshirish (ulanishdan oldin)
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=1008, reason="Token yaroqsiz")
        return

    # 2. user_id ni xavfsiz olish
    sub = payload.get("sub")
    if sub is None or not str(sub).isdigit():
        await websocket.close(code=1008, reason="Token yaroqsiz")
        return
    user_id = int(sub)

    # 3. Ulanishni qabul qilish va registry'ga qo'shish
    await ws_manager.connect(websocket, user_id)

    try:
        # 4. Xabar kutish sikli (ulanish ochiq turadi)
        while True:
            # Driver'dan event kutish (faqat matn/JSON)
            try:
                data = await websocket.receive_json()
            except (ValueError, TypeError):
                # Noto'g'ri JSON — ulanishni uzmaymiz, xato qaytaramiz
                await websocket.send_json({
                    "event": "error",
                    "data": {"message": "Noto'g'ri JSON format"},
                })
                continue

            event_type = data.get("event", "")
            response = await handle_event(event_type, data)
            await websocket.send_json(response)

    except WebSocketDisconnect:
        # Driver uzildi — registry'dan o'chirish (xotira tozalash)
        ws_manager.disconnect(user_id)
        logger.info(f"WebSocket uzildi: user_id={user_id}")

    except Exception as e:
        # Kutilmagan xato — toza yopish
        logger.error(f"WebSocket xatosi (user_id={user_id}): {e}")
        ws_manager.disconnect(user_id)
