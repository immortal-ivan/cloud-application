from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crypto import hash_password, verify_password
from app.data.database import get_db
from app.data.models import Role, User
from app.schemas import LoginRequest, TokenOut, UserOut, UserRegister
from app.security import bearer_scheme, get_current_user
from app.services.auth import create_auth_session, delete_auth_session, get_auth_session

router = APIRouter(prefix="/auth", tags=["Auth"])

DEFAULT_ROLE = "viewer"


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.name,
        permissions=sorted(user.permission_codes),
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать пользователя",
    description="Создаёт пользователя с ролью viewer. Пароль хранится только в виде хеша Argon2.",
    responses={409: {"description": "Логин или email уже заняты"}},
)
def register(data: UserRegister, db: Session = Depends(get_db)) -> UserOut:
    if db.scalar(select(User).where((User.username == data.username) | (User.email == data.email))):
        raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь с таким логином или email уже есть")
    role = db.scalar(select(Role).where(Role.name == DEFAULT_ROLE))
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Войти и получить токен",
    description="Проверяет логин и пароль и создаёт сеанс. Токен затем передаётся в `Authorization: Bearer ...`.",
    responses={401: {"description": "Неверный логин или пароль"}},
)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.username == data.username))
    # Одинаковая ошибка для неверного логина и пароля: не раскрываем, какой из них неверен.
    if user is None or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный логин или пароль")
    token, session = create_auth_session(db, user)
    return TokenOut(access_token=token, expires_at=session.expires_at)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Получить текущего пользователя",
    description="Требует действующий токен, но никакого специального разрешения.",
    responses={401: {"description": "Токен не передан или недействителен"}},
)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserOut:
    return user_out(current_user)


@router.get(
    "/session/{token}",
    summary="Проверить сеанс по токену",
    responses={404: {"description": "Сеанс не найден или истёк"}},
)
def read_session(token: str, db: Session = Depends(get_db)) -> dict:
    session = get_auth_session(db, token)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return {"user": session.user.username, "role": session.user.role.name, "expires_at": session.expires_at}


@router.delete(
    "/session/{token}",
    summary="Завершить сеанс",
    description="После удаления сеанса токен перестаёт действовать (дальнейшие запросы дают 401).",
    responses={404: {"description": "Сеанс не найден"}},
)
def delete_session(token: str, db: Session = Depends(get_db)) -> dict:
    if not delete_auth_session(db, token):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return {"message": "Session deleted"}


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выйти (завершить текущий сеанс)",
)
def logout(
    credentials=Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    delete_auth_session(db, credentials.credentials)
