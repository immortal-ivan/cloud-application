"""Схемы запросов и ответов API."""
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


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: str = "user"


class ServiceIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = ""
    status: str = Field(default="active", pattern="^(active|disabled)$")


class ServiceOut(ORM):
    id: int
    name: str
    description: str
    status: str


class FileOut(ORM):
    id: int
    original_name: str
    content_type: str
    size: int
    created_at: datetime
