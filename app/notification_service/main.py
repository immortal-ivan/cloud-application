"""Notification Service - отдельный FastAPI-сервис уведомлений (ЛР №29).

Запускается отдельным процессом/контейнером:
    python -m uvicorn app.notification_service.main:app --host 127.0.0.1 --port 9000
Уведомления хранятся в памяти процесса и исчезают при его перезапуске.
"""
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Notification Service", version="1.0.0")


class NotificationCreate(BaseModel):
    recipient: str = Field(..., min_length=3, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)
    # Ключ идемпотентности (доп. задание ЛР №30): повтор с тем же request_id
    # возвращает ранее созданное уведомление, а не создаёт новое.
    request_id: str | None = Field(default=None, max_length=64)


class NotificationResponse(BaseModel):
    id: int
    recipient: str
    message: str
    status: Literal["accepted"]


notifications: list[dict] = []
by_request_id: dict[str, dict] = {}


@app.get("/status", summary="Проверить состояние сервиса")
def status():
    return {"service": "notification", "status": "running"}


@app.post(
    "/notifications",
    response_model=NotificationResponse,
    status_code=201,
    summary="Принять уведомление",
)
def create_notification(notification: NotificationCreate):
    if notification.request_id and notification.request_id in by_request_id:
        return by_request_id[notification.request_id]
    item = {
        "id": len(notifications) + 1,
        "recipient": notification.recipient,
        "message": notification.message,
        "status": "accepted",
    }
    notifications.append(item)
    if notification.request_id:
        by_request_id[notification.request_id] = item
    return item


@app.get(
    "/notifications",
    response_model=list[NotificationResponse],
    summary="Получить принятые уведомления",
)
def get_notifications():
    return notifications


@app.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
    summary="Получить уведомление по id",
)
def get_notification(notification_id: int):
    for item in notifications:
        if item["id"] == notification_id:
            return item
    raise HTTPException(status_code=404, detail="Notification not found")


@app.get("/test/error/{status_code}", summary="Сформировать тестовую ошибку")
def test_error(status_code: int):
    """Учебный endpoint ЛР №30 для исследования HTTPStatusError."""
    raise HTTPException(status_code=status_code, detail="Test service error")
