from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, oauth2_scheme
from app.models import AccessToken, User
from app.schemas import TokenOut, UserOut
from app.security import hash_token, new_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.name,
        permissions=sorted(user.permission_codes),
    )


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenOut:
    """Вход по логину и паролю (форма OAuth2). Возвращает Bearer-токен."""
    user = db.scalar(select(User).where(User.username == form.username))
    # Одинаковая ошибка для неверного логина и пароля: не раскрываем, какой из них неверен.
    if user is None or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный логин или пароль")

    token, token_hash, expires = new_token()
    db.add(AccessToken(token_hash=token_hash, user_id=user.id, expires_at=expires))
    db.commit()
    return TokenOut(access_token=token, expires_at=expires)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return user_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: str = Depends(oauth2_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    db.execute(delete(AccessToken).where(AccessToken.token_hash == hash_token(token)))
    db.commit()
