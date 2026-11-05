"""Схемы запросов и ответов API."""
from app.schemas.services import ServiceCreate, ServiceOut  # noqa: F401
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserOut(ORM):
    id: int
    username: str
    email: str
    role: str
    permissions: list[str]


class UserRegister(BaseModel):
    """Саморегистрация (ЛР №19): новый пользователь получает роль viewer."""

    username: str = Field(min_length=3, max_length=50, examples=["student01"])
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120, examples=["student01@example.com"])
    password: str = Field(min_length=8, max_length=128, examples=["Student#2026"])


class LoginRequest(BaseModel):
    username: str = Field(examples=["student01"])
    password: str = Field(examples=["Student#2026"])


class RoleChange(BaseModel):
    role: str = Field(description="Имя новой роли", examples=["operator"])


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: str = "viewer"


class FileOut(ORM):
    id: int
    original_name: str
    content_type: str
    size: int
    created_at: datetime
