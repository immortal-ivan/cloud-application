from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import User
from app.schemas.services import ServiceCreate, ServiceOut
from app.security import require_permission
from app.services import services as service_layer

router = APIRouter(prefix="/services", tags=["Services"])

ServiceId = Annotated[int, Path(description="Уникальный идентификатор сервиса", gt=0, examples=[1])]
NOT_FOUND = {404: {"description": "Сервис не найден"}}
AUTH_ERRORS = {
    401: {"description": "Токен не передан или недействителен"},
    403: {"description": "Недостаточно прав (нужно разрешение services.read / services.write)"},
}


@router.get(
    "",
    response_model=list[ServiceOut],
    summary="Получить список сервисов",
    description=(
        "Возвращает все облачные сервисы. Необязательный параметр `status` "
        "оставляет только сервисы в указанном состоянии. Требуется разрешение `services.read`."
    ),
    responses=AUTH_ERRORS,
)
def read_services(
    status_filter: Annotated[
        str | None,
        Query(alias="status", pattern="^(running|maintenance|stopped)$", description="Фильтр по состоянию"),
    ] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("services.read")),
):
    if status_filter:
        return service_layer.get_services_by_status(db, status_filter)
    return service_layer.get_all_services(db)


@router.get(
    "/{service_id}",
    response_model=ServiceOut,
    summary="Получить сервис по идентификатору",
    description="Возвращает сведения об одном облачном сервисе. Идентификатор передаётся в адресе запроса.",
    responses={**NOT_FOUND, **AUTH_ERRORS},
)
def read_service(
    service_id: ServiceId,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("services.read")),
):
    found = service_layer.get_service_by_id(db, service_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
    return found


@router.post(
    "",
    response_model=ServiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый сервис",
    description="Создаёт новый облачный сервис на основе переданных данных. Требуется `services.write`.",
    responses={
        400: {"description": "Указанный тип сервиса не найден"},
        409: {"description": "Сервис с таким названием уже существует"},
        **AUTH_ERRORS,
    },
)
def create_service_endpoint(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("services.write")),
):
    if service_layer.name_is_taken(db, service.name):
        raise HTTPException(status.HTTP_409_CONFLICT, "Service name already exists")
    created = service_layer.create_service(db, service)
    if created is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Service type not found")
    return created


@router.put(
    "/{service_id}",
    response_model=ServiceOut,
    summary="Изменить сервис",
    description="Полностью заменяет данные существующего сервиса. Требуется `services.write`.",
    responses={400: {"description": "Указанный тип сервиса не найден"}, **NOT_FOUND, **AUTH_ERRORS},
)
def update_service_endpoint(
    service_id: ServiceId,
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("services.write")),
):
    if service_layer.get_service_by_id(db, service_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
    if service_layer.get_service_type(db, service.type) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Service type not found")
    if service_layer.name_is_taken(db, service.name, except_id=service_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Service name already exists")
    return service_layer.update_service(db, service_id, service)


@router.delete(
    "/{service_id}",
    summary="Удалить сервис",
    description="Удаляет сервис с указанным идентификатором. Требуется `services.write`.",
    responses={**NOT_FOUND, **AUTH_ERRORS},
)
def delete_service_endpoint(
    service_id: ServiceId,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("services.write")),
):
    if not service_layer.delete_service(db, service_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
    return {"message": "Service deleted", "id": service_id}
