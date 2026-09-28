from fastapi import FastAPI

from app.config import APP_NAME, APP_VERSION
from app.routers.services import router as services_router
from app.routers.system import router as system_router

tags_metadata = [
    {
        "name": "Services",
        "description": (
            "Операции управления программными "
            "сервисами Cloud Application."
        )
    },
    {
        "name": "System",
        "description": "Системные методы приложения."
    }
]

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Учебное серверное приложение для изучения "
        "разработки программного обеспечения облачных систем."
    ),
    openapi_tags=tags_metadata
)

app.include_router(services_router)
app.include_router(system_router)


@app.get("/")
def root():
    return {"application": APP_NAME, "version": APP_VERSION, "status": "running"}


@app.get("/course")
def course():
    return {
        "discipline": "Управление работами и разработка ПО облачных систем",
        "laboratory": 7,
        "project": APP_NAME
    }