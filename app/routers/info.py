"""Информационные маршруты (ЛР №2): корень, состояние, сведения о приложении, курс."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.data.database import get_db

router = APIRouter(tags=["Info"])


@router.get("/", summary="Основная информация о приложении")
def root() -> dict:
    return {"application": settings.app_name, "version": settings.app_version, "status": "running"}


@router.get("/status", summary="Состояние приложения")
def get_status(db: Session = Depends(get_db)) -> dict:
    """Приложение живо, база отвечает.

    Если БД недоступна (например, контейнер приложения запущен без PostgreSQL),
    маршрут всё равно отвечает 200 и сообщает "database": "unavailable".
    """
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        database = "unavailable"
    return {
        "status": "ok",
        "service": settings.app_name,
        "app": settings.app_name,
        "version": settings.app_version,
        "database": database,
    }


@router.get("/about", summary="Сведения о серверном приложении")
def about() -> dict:
    return {
        "name": settings.app_name,
        "type": "server application",
        "language": "Python",
        "framework": "FastAPI",
    }


@router.get("/course", summary="Сведения о дисциплине и лабораторной работе")
def course() -> dict:
    return {
        "discipline": "Управление работами и разработка программного обеспечения облачных систем",
        "laboratory": 2,
        "project": settings.app_name,
    }
