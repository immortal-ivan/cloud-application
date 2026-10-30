from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

router = APIRouter(tags=["status"])


@router.get("/status")
def get_status(db: Session = Depends(get_db)) -> dict:
    """Диагностический маршрут: приложение живо, база отвечает."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version, "database": "ok"}
