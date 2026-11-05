"""Объектное хранилище (ЛР №18): содержимое - в каталоге STORAGE_PATH, метаданные - в PostgreSQL."""
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.data.models import StoredObject


def object_to_dict(obj: StoredObject) -> dict:
    return {
        "id": obj.id,
        "original_name": obj.original_name,
        "content_type": obj.content_type,
        "size_bytes": obj.size_bytes,
        "created_at": obj.created_at,
        "download_url": f"/objects/{obj.id}/download",
    }


async def save_object(db: Session, file: UploadFile) -> StoredObject:
    # Path(...).name отбрасывает каталоги из имени, присланного клиентом (../../x.txt -> x.txt)
    original_name = Path(file.filename or "file").name
    extension = Path(original_name).suffix.lower()
    storage_name = f"{uuid4().hex}{extension}"  # внутреннее имя - ключ объекта

    storage_directory = Path(settings.storage_path)
    storage_directory.mkdir(parents=True, exist_ok=True)
    file_path = storage_directory / storage_name

    size_bytes = 0
    try:
        with file_path.open("wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # запись блоками по 1 МБ
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > settings.max_upload_size:
                    raise HTTPException(
                        status.HTTP_413_CONTENT_TOO_LARGE,
                        f"File is larger than {settings.max_upload_size} bytes",
                    )
                buffer.write(chunk)
        obj = StoredObject(
            original_name=original_name,
            storage_name=storage_name,
            content_type=file.content_type,
            size_bytes=size_bytes,
            storage_path=str(file_path),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except Exception:
        db.rollback()
        if file_path.exists():  # неполный файл не остаётся в хранилище
            file_path.unlink()
        raise
    finally:
        await file.close()


def get_objects(db: Session) -> list[StoredObject]:
    return list(db.scalars(select(StoredObject).order_by(StoredObject.id)).all())


def get_object(db: Session, object_id: int) -> StoredObject | None:
    return db.get(StoredObject, object_id)


def delete_object(db: Session, obj: StoredObject) -> None:
    """Удаляются и файл, и запись метаданных."""
    file_path = Path(obj.storage_path)
    if file_path.exists():
        file_path.unlink()
    db.delete(obj)
    db.commit()
