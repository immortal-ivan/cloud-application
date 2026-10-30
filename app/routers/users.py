from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.models import Role, User
from app.routers.auth import user_out
from app.schemas import UserCreate, UserOut
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(require_permission("users:read")), db: Session = Depends(get_db)):
    return [user_out(u) for u in db.scalars(select(User).order_by(User.id))]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    _: User = Depends(require_permission("users:write")),
    db: Session = Depends(get_db),
):
    role = db.scalar(select(Role).where(Role.name == data.role))
    if role is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Роль «{data.role}» не существует")
    if db.scalar(select(User).where((User.username == data.username) | (User.email == data.email))):
        raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь с таким логином или email уже есть")

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
