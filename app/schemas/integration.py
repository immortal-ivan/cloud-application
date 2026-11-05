"""Схемы маршрутов интеграции с Notification Service."""
from pydantic import BaseModel, Field


class NotificationSendRequest(BaseModel):
    recipient: str = Field(..., min_length=3, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)


class NotificationSendResponse(BaseModel):
    id: int
    recipient: str
    message: str
    status: str
