from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import User
from app.schemas.objects import StoredObjectResponse
from app.security import require_permission
from app.services.objects import delete_object, get_object, get_objects, object_to_dict, save_object

router = APIRouter(prefix="/objects", tags=["Objects"])

ERRORS = {
    401: {"description": "Токен не передан или недействителен"},
    403: {"description": "Недостаточно прав (objects.read / objects.write)"},
}
NOT_FOUND = {404: {"description": "Object not found"}}


def _get_or_404(db: Session, object_id: int):
    obj = get_object(db, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    return obj


@router.post(
    "",
    response_model=StoredObjectResponse,
    status_code=201,
    summary="Загрузить объект",
    description="Принимает файл (multipart/form-data) размером не более MAX_UPLOAD_SIZE. Требуется `objects.write`.",
    responses={413: {"description": "Файл больше допустимого размера"}, **ERRORS},
)
async def upload_object(
    file: Annotated[UploadFile, File(description="Файл для сохранения в объектном хранилище")],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("objects.write")),
):
    obj = await save_object(db, file)
    return object_to_dict(obj)


@router.get(
    "",
    response_model=list[StoredObjectResponse],
    summary="Получить список объектов",
    description="Требуется `objects.read`.",
    responses=ERRORS,
)
def read_objects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("objects.read")),
):
    return [object_to_dict(obj) for obj in get_objects(db)]


@router.get(
    "/{object_id}",
    response_model=StoredObjectResponse,
    summary="Получить сведения об объекте",
    description="Возвращает метаданные без физического пути. Требуется `objects.read`.",
    responses={**NOT_FOUND, **ERRORS},
)
def read_object(
    object_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("objects.read")),
):
    return object_to_dict(_get_or_404(db, object_id))


@router.get(
    "/{object_id}/download",
    summary="Скачать объект",
    description="Отдаёт содержимое под исходным именем файла. Требуется `objects.read`.",
    responses={**NOT_FOUND, **ERRORS},
)
def download_object(
    object_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("objects.read")),
):
    obj = _get_or_404(db, object_id)
    file_path = Path(obj.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found")
    return FileResponse(
        path=str(file_path),
        media_type=obj.content_type or "application/octet-stream",
        filename=obj.original_name,
    )


@router.delete(
    "/{object_id}",
    summary="Удалить объект",
    description="Удаляет файл из хранилища и запись из PostgreSQL. Требуется `objects.write`.",
    responses={**NOT_FOUND, **ERRORS},
)
def remove_object(
    object_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("objects.write")),
):
    obj = _get_or_404(db, object_id)
    delete_object(db, obj)
    return {"message": "Object deleted", "id": object_id}
