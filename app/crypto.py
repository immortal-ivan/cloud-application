"""Безопасное хранение паролей (Argon2 через pwdlib) и токены доступа."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash

from app.config import settings

# PasswordHash.recommended() использует Argon2.
_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def new_token() -> tuple[str, str, datetime]:
    """Возвращает (токен для клиента, SHA-256 для БД, момент истечения)."""
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.token_ttl_minutes)
    return token, hash_token(token), expires


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
