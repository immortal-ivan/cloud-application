"""Начальные данные: права, роли, учебные пользователи и услуги.

Запуск:  python -m scripts.seed
Скрипт можно запускать повторно: существующие записи не дублируются.
Пароли учебных пользователей берутся из переменных окружения
SEED_ADMIN_PASSWORD / SEED_USER_PASSWORD (значения по умолчанию - только для обучения).
"""
import os

from sqlalchemy import select

from app.data.database import SessionLocal
from app.data.models import Permission, Role, Service, ServiceType, User
from app.crypto import hash_password

PERMISSIONS = {
    "services.read": "Просмотр каталога сервисов",
    "services.write": "Создание, изменение и удаление сервисов",
    "objects.read": "Просмотр и скачивание объектов хранилища",
    "objects.write": "Загрузка и удаление объектов хранилища",
    "files.read": "Просмотр своих файлов",
    "files.write": "Загрузка файлов",
    "files.read_all": "Просмотр файлов всех пользователей",
    "users.manage": "Просмотр и создание пользователей",
    "roles.manage": "Управление ролями пользователей",
}

ROLES = {
    "viewer": ["services.read", "objects.read", "files.read", "files.write"],
    "operator": [
        "services.read", "services.write", "objects.read", "objects.write", "files.read", "files.write",
    ],
    "administrator": list(PERMISSIONS),
    # Дополнительная роль из ЛР №20: работает без изменения кода защищаемых маршрутов
    "content_manager": ["objects.read", "objects.write", "services.read"],
}

SERVICE_TYPES = [
    ("application", "Прикладной сервис"),
    ("database", "Сервис базы данных"),
    ("monitoring", "Сервис мониторинга"),
]

SERVICES = [
    ("Web Service", "application", "Веб-приложение", "running"),
    ("Database Service", "database", "Сервер PostgreSQL", "running"),
    ("Monitoring Service", "monitoring", "Сбор метрик", "running"),
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
            ("admin", "admin@example.com", admin_password, "administrator"),
            ("student01", "student01@example.com", user_password, "viewer"),
            ("student02", "student02@example.com", user_password, "operator"),
            ("student03", "student03@example.com", user_password, "administrator"),
        ]:
            if db.scalar(select(User).where(User.username == username)) is None:
                db.add(User(username=username, email=email, password_hash=hash_password(password), role_id=roles[role].id))

        types = {}
        for name, description in SERVICE_TYPES:
            st = db.scalar(select(ServiceType).where(ServiceType.name == name))
            if st is None:
                st = ServiceType(name=name, description=description)
                db.add(st)
            types[name] = st
        db.flush()

        for name, type_name, description, status in SERVICES:
            if db.scalar(select(Service).where(Service.name == name)) is None:
                db.add(Service(name=name, type_id=types[type_name].id, description=description, status=status))

        db.commit()
    print("Начальные данные загружены.")


if __name__ == "__main__":
    main()
