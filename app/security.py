"""Программная авторизация (ЛР №21): текущий пользователь по Bearer-токену и проверка разрешений.

Аутентификация отвечает на вопрос «кто выполняет запрос» (401, если токена нет или он
недействителен), авторизация - «разрешено ли ему это» (403, если нет нужного permission).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import User
from app.services.auth import get_auth_session

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized("Authentication required")
    if credentials.scheme.lower() != "bearer":
        raise _unauthorized("Invalid authentication scheme")
    session = get_auth_session(db, credentials.credentials)
    if session is None:
        raise _unauthorized("Invalid or expired session")
    # Роль и разрешения читаются из БД при каждом запросе, поэтому смена роли действует сразу.
    return session.user


def _permissions_of(user: User) -> set[str]:
    return {p.code for p in user.role.permissions} if user.role is not None else set()


def require_permission(permission_code: str):
    """Зависимость: пропускает пользователя, у роли которого есть permission_code."""

    def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
        if permission_code not in _permissions_of(current_user):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Insufficient permissions: {permission_code}")
        return current_user

    return permission_dependency


def require_any_permission(*permission_codes: str):
    """Зависимость: достаточно любого одного из перечисленных разрешений."""

    def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role is None or not (_permissions_of(current_user) & set(permission_codes)):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Insufficient permissions: one of " + ", ".join(permission_codes),
            )
        return current_user

    return permission_dependency
