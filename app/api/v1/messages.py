from fastapi import APIRouter, Depends, File, UploadFile, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_operator
from app.models.user import User
from app.schemas.message import (
    MessageResponse,
    ActiveMessageResponse,
    ActiveMessageListResponse,
)
from app.services.message import message_service
from app.services.websocket import websocket_service
from app.redis.cache import get_voice_audio, get_voice_meta, get_voice_ttl, list_active_messages
from app.utils.helpers import build_audio_url

router = APIRouter(prefix="/messages", tags=["Voice Messages"])


@router.post(
    "/broadcast",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Umumiy xabar (barcha online driverlarga)",
)
async def send_broadcast(
    file: UploadFile = File(..., description="Ovozli xabar (max 20s)"),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):

    meta, online_user_ids = await message_service.send_broadcast(
        db=db, sender=current_user, file=file,
    )

    # Real-time auto-play yetkazish
    delivered = await websocket_service.deliver_broadcast(online_user_ids, meta)

    return MessageResponse(
        id=meta.message_id,
        sender_id=meta.sender_id,
        sender_name=meta.sender_name,
        recipient_id=None,
        message_type=meta.message_type,
        audio_url=build_audio_url(meta.message_id),
        delivered_to=delivered,
        expires_in=settings.VOICE_MESSAGE_TTL,
        created_at=meta.created_at,
    )


@router.post(
    "/private/{driver_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Shaxsiy xabar (bitta driverga)",
)
async def send_private(
    driver_id: int,
    file: UploadFile = File(..., description="Ovozli xabar (max 20s)"),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):

    meta, driver_user_id = await message_service.send_private(
        db=db, sender=current_user, file=file, driver_id=driver_id,
    )

    delivered = await websocket_service.deliver_private(driver_user_id, meta)

    return MessageResponse(
        id=meta.message_id,
        sender_id=meta.sender_id,
        sender_name=meta.sender_name,
        recipient_id=meta.recipient_id,
        message_type=meta.message_type,
        audio_url=build_audio_url(meta.message_id),
        delivered_to=1 if delivered else 0,
        expires_in=settings.VOICE_MESSAGE_TTL,
        created_at=meta.created_at,
    )


@router.get(
    "/active",
    response_model=ActiveMessageListResponse,
    summary="Aktiv xabarlar (60s ichida)",
)
async def get_active_messages(
    current_user: User = Depends(get_current_user),
):

    metas = await list_active_messages()
    items = []
    for m in metas:
        ttl = await get_voice_ttl(m.message_id)
        if ttl <= 0:
            continue
        items.append(
            ActiveMessageResponse(
                id=m.message_id,
                sender_name=m.sender_name,
                message_type=m.message_type,
                recipient_id=m.recipient_id,
                audio_url=build_audio_url(m.message_id),
                seconds_remaining=ttl,
                created_at=m.created_at,
            )
        )
    return ActiveMessageListResponse(messages=items, total=len(items))


@router.get(
    "/{message_id}/audio",
    summary="Audio'ni olish (60s ichida)",
)
async def get_message_audio(
    message_id: int,
    current_user: User = Depends(get_current_user),
):

    meta = await get_voice_meta(message_id)
    audio = await get_voice_audio(message_id)

    if meta is None or audio is None:
        return Response(
            content=b'{"detail":"Xabar muddati o\'tgan yoki topilmadi"}',
            status_code=status.HTTP_404_NOT_FOUND,
            media_type="application/json",
        )

    return Response(content=audio, media_type=meta.content_type)
