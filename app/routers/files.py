"""Загрузка и скачивание файлов (нужен python-multipart)."""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, require_permission
from app.models import StoredFile, User
from app.schemas import FileOut

router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile = File(...),
    user: User = Depends(require_permission("files:write")),
    db: Session = Depends(get_db),
):
    limit = settings.max_upload_mb * 1024 * 1024
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"Файл больше {settings.max_upload_mb} МБ")

    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    stored_name = uuid.uuid4().hex  # имя на диске не зависит от имени, присланного клиентом
    (settings.storage_dir / stored_name).write_bytes(content)

    record = StoredFile(
        owner_id=user.id,
        original_name=(file.filename or "file")[:255],
        stored_name=stored_name,
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[FileOut])
def list_files(user: User = Depends(require_permission("files:read")), db: Session = Depends(get_db)):
    query = select(StoredFile).order_by(StoredFile.id)
    if "files:read_all" not in user.permission_codes:
        query = query.where(StoredFile.owner_id == user.id)
    return db.scalars(query).all()


@router.get("/{file_id}/download")
def download(file_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.get(StoredFile, file_id)
    allowed = record is not None and (
        record.owner_id == user.id or "files:read_all" in user.permission_codes
    )
    if not allowed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не найден")
    return FileResponse(
        settings.storage_dir / record.stored_name,
        media_type=record.content_type,
        filename=record.original_name,
    )
