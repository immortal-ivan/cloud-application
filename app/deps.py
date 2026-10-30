"""Зависимости FastAPI: текущий пользователь и проверка прав (авторизация)."""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AccessToken, User
from app.security import hash_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Недействительный или просроченный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    row = db.scalar(select(AccessToken).where(AccessToken.token_hash == hash_token(token)))
    if row is None:
        raise unauthorized

    expires = row.expires_at
    if expires.tzinfo is None:  # SQLite возвращает время без часового пояса
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc) or not row.user.is_active:
        raise unauthorized
    return row.user


def require_permission(code: str):
    """Фабрика зависимости: пропускает только пользователей с нужным правом."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if code not in user.permission_codes:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Недостаточно прав: нужно право «{code}»")
        return user

    return checker
