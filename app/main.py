"""Точка входа REST API Cloud Application."""
from fastapi import FastAPI

from app.config import settings
from app.routers import auth, files, services, status, users

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Учебный облачный сервис: аутентификация, роли и права, каталог услуг, файлы.",
)

app.include_router(status.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(services.router)
app.include_router(files.router)
