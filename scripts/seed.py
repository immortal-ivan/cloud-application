"""Начальные данные: права, роли, учебные пользователи и услуги.

Запуск:  python -m scripts.seed
Скрипт можно запускать повторно: существующие записи не дублируются.
Пароли учебных пользователей берутся из переменных окружения
SEED_ADMIN_PASSWORD / SEED_USER_PASSWORD (значения по умолчанию - только для обучения).
"""
import os

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Permission, Role, Service, User
from app.security import hash_password

PERMISSIONS = {
    "services:read": "Просмотр каталога услуг",
    "services:write": "Создание, изменение и удаление услуг",
    "files:read": "Просмотр своих файлов",
    "files:write": "Загрузка файлов",
    "files:read_all": "Просмотр файлов всех пользователей",
    "users:read": "Просмотр списка пользователей",
    "users:write": "Создание пользователей",
}

ROLES = {
    "admin": list(PERMISSIONS),
    "user": ["services:read", "files:read", "files:write"],
}

SERVICES = [
    ("Виртуальный сервер", "Облачная виртуальная машина", "active"),
    ("Хранилище файлов", "Объектное хранилище для файлов пользователей", "active"),
    ("Резервное копирование", "Ежедневные копии баз данных", "disabled"),
]


def main() -> None:
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "Admin#2026")
    user_password = os.getenv("SEED_USER_PASSWORD", "Student#2026")

    with SessionLocal() as db:
        perms = {}
        for code, description in PERMISSIONS.items():
            perm = db.scalar(select(Permission).where(Permission.code == code))
            if perm is None:
                perm = Permission(code=code, description=description)
                db.add(perm)
            perms[code] = perm
        db.flush()

        roles = {}
        for name, codes in ROLES.items():
            role = db.scalar(select(Role).where(Role.name == name))
            if role is None:
                role = Role(name=name)
                db.add(role)
            role.permissions = [perms[c] for c in codes]
            roles[name] = role
        db.flush()

        for username, email, password, role in [
            ("admin", "admin@example.com", admin_password, "admin"),
            ("student", "student@example.com", user_password, "user"),
        ]:
            if db.scalar(select(User).where(User.username == username)) is None:
                db.add(User(username=username, email=email, password_hash=hash_password(password), role_id=roles[role].id))

        for name, description, status in SERVICES:
            if db.scalar(select(Service).where(Service.name == name)) is None:
                db.add(Service(name=name, description=description, status=status))

        db.commit()
    print("Начальные данные загружены.")


if __name__ == "__main__":
    main()
