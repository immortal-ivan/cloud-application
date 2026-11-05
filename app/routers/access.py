"""Управление доступом (ЛР №20-21): роли, пользователи, назначение ролей."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import Role, User
from app.routers.auth import user_out
from app.schemas import RoleChange, UserOut
from app.security import require_any_permission, require_permission

router = APIRouter(prefix="/access", tags=["Access"])

ERRORS = {
    401: {"description": "Токен не передан или недействителен"},
    403: {"description": "Недостаточно прав"},
}


@router.get(
    "/roles",
    summary="Список ролей и их разрешений",
    description="Требуется разрешение `roles.manage`.",
    responses=ERRORS,
)
def read_roles(db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.manage"))):
    roles = db.scalars(select(Role).order_by(Role.id)).all()
    return [{"id": r.id, "name": r.name, "permissions": sorted(p.code for p in r.permissions)} for r in roles]


@router.get(
    "/summary",
    summary="Краткая сводка доступа (учебный маршрут)",
    description="Доступен при наличии хотя бы одного из разрешений `users.manage` или `roles.manage`.",
    responses=ERRORS,
)
def read_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("users.manage", "roles.manage")),
):
    users = db.scalars(select(User)).all()
    by_role: dict[str, int] = {}
    for u in users:
        by_role[u.role.name] = by_role.get(u.role.name, 0) + 1
    return {"requested_by": current_user.username, "users_total": len(users), "users_by_role": by_role}


@router.get(
    "/users/{user_id}",
    response_model=UserOut,
    summary="Сведения о пользователе",
    description="Требуется разрешение `users.manage`.",
    responses={404: {"description": "Пользователь не найден"}, **ERRORS},
)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user_out(user)


@router.put(
    "/users/{user_id}/role",
    response_model=UserOut,
    summary="Назначить пользователю роль",
    description="Требуется `roles.manage`. Изменение действует сразу, токен менять не нужно.",
    responses={404: {"description": "Пользователь или роль не найдены"}, **ERRORS},
)
def change_user_role(
    user_id: int,
    data: RoleChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    role = db.scalar(select(Role).where(Role.name == data.role))
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    user.role_id = role.id
    db.commit()
    db.refresh(user)
    return user_out(user)
