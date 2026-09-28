from fastapi import APIRouter

from app.config import APP_NAME, APP_VERSION
from app.services.services import count_services

router = APIRouter(tags=["System"])


@router.get("/status", summary="Состояние приложения")
def status():
    return {"status": "ok", "service": APP_NAME}


@router.get("/about", summary="Информация о приложении")
def about():
    return {
        "name": APP_NAME,
        "type": "server application",
        "language": "Python",
        "framework": "FastAPI"
    }


@router.get("/service-count", summary="Количество сервисов")
def service_count():
    return {"services": count_services()}