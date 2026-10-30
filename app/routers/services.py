from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.models import Service, User
from app.schemas import ServiceIn, ServiceOut

router = APIRouter(prefix="/services", tags=["services"])


def get_or_404(db: Session, service_id: int) -> Service:
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Услуга не найдена")
    return service


@router.get("", response_model=list[ServiceOut])
def list_services(_: User = Depends(require_permission("services:read")), db: Session = Depends(get_db)):
    return db.scalars(select(Service).order_by(Service.id)).all()


@router.get("/{service_id}", response_model=ServiceOut)
def read_service(
    service_id: int,
    _: User = Depends(require_permission("services:read")),
    db: Session = Depends(get_db),
):
    return get_or_404(db, service_id)


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    data: ServiceIn,
    _: User = Depends(require_permission("services:write")),
    db: Session = Depends(get_db),
):
    if db.scalar(select(Service).where(Service.name == data.name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Услуга с таким названием уже есть")
    service = Service(**data.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    data: ServiceIn,
    _: User = Depends(require_permission("services:write")),
    db: Session = Depends(get_db),
):
    service = get_or_404(db, service_id)
    for key, value in data.model_dump().items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    _: User = Depends(require_permission("services:write")),
    db: Session = Depends(get_db),
):
    db.delete(get_or_404(db, service_id))
    db.commit()
