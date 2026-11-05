"""Маршруты, через которые Cloud Application обращается к Notification Service."""
from fastapi import APIRouter, Depends, status

from app.deps import require_permission
from app.integrations.notification_client import get_notification, send_notification
from app.models import User
from app.schemas.integration import NotificationSendRequest, NotificationSendResponse

router = APIRouter(prefix="/integration", tags=["Integration"])


@router.post(
    "/notifications",
    response_model=NotificationSendResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Передать уведомление внутреннему сервису",
)
async def forward_notification(
    notification: NotificationSendRequest,
    current_user: User = Depends(require_permission("services:write")),
):
    result = await send_notification(
        recipient=notification.recipient,
        message=notification.message,
    )
    return result


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationSendResponse,
    summary="Получить уведомление из внутреннего сервиса",
)
async def read_notification(
    notification_id: int,
    current_user: User = Depends(require_permission("services:read")),
):
    return await get_notification(notification_id)
