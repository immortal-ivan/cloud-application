"""Маршруты, через которые Cloud Application обращается к Notification Service.

Ошибки интеграции преобразуются в контролируемые ответы:
503 - сервис недоступен, 504 - не ответил вовремя, 502 - вернул ошибочный HTTP-ответ.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import require_permission
from app.integrations.notification_client import (
    NotificationServiceBadResponse,
    NotificationServiceTimeout,
    NotificationServiceUnavailable,
    get_notification,
    send_notification,
)
from app.models import User
from app.schemas.integration import NotificationSendRequest, NotificationSendResponse

router = APIRouter(prefix="/integration", tags=["Integration"])

INTEGRATION_ERRORS = {
    "timeout": (status.HTTP_504_GATEWAY_TIMEOUT, "Notification service response timeout"),
    "unavailable": (status.HTTP_503_SERVICE_UNAVAILABLE, "Notification service is unavailable"),
    "bad_response": (status.HTTP_502_BAD_GATEWAY, "Notification service returned an invalid response"),
}


def _http_error(kind: str) -> HTTPException:
    code, detail = INTEGRATION_ERRORS[kind]
    return HTTPException(status_code=code, detail=detail)


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
    try:
        result = await send_notification(
            recipient=notification.recipient,
            message=notification.message,
        )
        return result
    except NotificationServiceTimeout as exc:
        raise _http_error("timeout") from exc
    except NotificationServiceUnavailable as exc:
        raise _http_error("unavailable") from exc
    except NotificationServiceBadResponse as exc:
        raise _http_error("bad_response") from exc


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationSendResponse,
    summary="Получить уведомление из внутреннего сервиса",
)
async def read_notification(
    notification_id: int,
    current_user: User = Depends(require_permission("services:read")),
):
    try:
        result = await get_notification(notification_id)
    except NotificationServiceTimeout as exc:
        raise _http_error("timeout") from exc
    except NotificationServiceUnavailable as exc:
        raise _http_error("unavailable") from exc
    except NotificationServiceBadResponse as exc:
        raise _http_error("bad_response") from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return result
