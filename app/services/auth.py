"""Сеансы пользователей (ЛР №19): создание, поиск по токену, завершение."""
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.crypto import hash_token, new_token
from app.data.models import AuthSession, User


def create_auth_session(db: Session, user: User) -> tuple[str, AuthSession]:
    token, token_hash, expires = new_token()
    session = AuthSession(token_hash=token_hash, user_id=user.id, expires_at=expires)
    db.add(session)
    db.commit()
    return token, session


def get_auth_session(db: Session, token: str) -> AuthSession | None:
    """Действующий сеанс по токену либо None (нет сеанса, истёк или пользователь отключён)."""
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(token)))
    if session is None:
        return None
    expires = session.expires_at
    if expires.tzinfo is None:  # SQLite возвращает время без часового пояса
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc) or not session.user.is_active:
        return None
    return session


def delete_auth_session(db: Session, token: str) -> bool:
    result = db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_token(token)))
    db.commit()
    return result.rowcount > 0
