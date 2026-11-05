"""Точка входа REST API Cloud Application."""
from fastapi import FastAPI

from app.config import settings
from app.routers import access, auth, files, info, objects, services, users
from app.routers.integration import router as integration_router

tags_metadata = [
    {"name": "Info", "description": "Состояние и сведения о приложении."},
    {"name": "Auth", "description": "Регистрация, вход, текущий пользователь и сеансы."},
    {"name": "Services", "description": "Операции управления программными сервисами Cloud Application."},
    {"name": "Objects", "description": "Объектное хранилище: файлы в каталоге, метаданные в PostgreSQL."},
    {"name": "Access", "description": "Роли и разрешения (только для администраторов)."},
    {"name": "files", "description": "Личные файлы пользователя."},
    {"name": "users", "description": "Управление учётными записями."},
    {"name": "Integration", "description": "Обращение к Notification Service."},
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Учебное серверное приложение для изучения разработки программного обеспечения "
        "облачных систем: каталог сервисов, объектное хранилище, пользователи, роли и разрешения. "
        "Защищённые операции требуют заголовок `Authorization: Bearer <token>`."
    ),
    openapi_tags=tags_metadata,
)

for router in (
    info.router,
    auth.router,
    users.router,
    services.router,
    objects.router,
    files.router,
    access.router,
    integration_router,
):
    app.include_router(router)
