"""Сервисный слой ресурса /services: бизнес-логика и обращение к БД через ORM (ЛР №15)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import Service, ServiceType
from app.schemas.services import ServiceCreate


def service_to_dict(service: Service) -> dict:
    """В БД хранится type_id, а REST API по-прежнему возвращает название типа."""
    return {
        "id": service.id,
        "name": service.name,
        "type": service.service_type.name,
        "status": service.status,
        "description": service.description,
    }


def get_all_services(db: Session) -> list[dict]:
    services = db.scalars(select(Service).order_by(Service.id)).all()
    return [service_to_dict(s) for s in services]


def get_service_by_id(db: Session, service_id: int) -> dict | None:
    service = db.get(Service, service_id)
    return None if service is None else service_to_dict(service)


def get_services_by_status(db: Session, status: str) -> list[dict]:
    statement = select(Service).where(Service.status == status).order_by(Service.id)
    return [service_to_dict(s) for s in db.scalars(statement).all()]


def get_service_type(db: Session, type_name: str) -> ServiceType | None:
    return db.scalar(select(ServiceType).where(ServiceType.name == type_name))


def name_is_taken(db: Session, name: str, except_id: int | None = None) -> bool:
    found = db.scalar(select(Service).where(Service.name == name))
    return found is not None and found.id != except_id


def create_service(db: Session, data: ServiceCreate) -> dict | None:
    """Возвращает None, если указанного типа сервиса нет в service_types."""
    service_type = get_service_type(db, data.type)
    if service_type is None:
        return None
    service = Service(
        name=data.name,
        description=data.description,
        status=data.status,
        type_id=service_type.id,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service_to_dict(service)


def update_service(db: Session, service_id: int, data: ServiceCreate) -> dict | None:
    """None - сервиса нет; сначала проверьте тип через get_service_type."""
    service = db.get(Service, service_id)
    service_type = get_service_type(db, data.type)
    if service is None or service_type is None:
        return None
    service.name = data.name
    service.description = data.description
    service.status = data.status
    service.type_id = service_type.id
    db.commit()
    db.refresh(service)
    return service_to_dict(service)


def delete_service(db: Session, service_id: int) -> bool:
    service = db.get(Service, service_id)
    if service is None:
        return False
    db.delete(service)
    db.commit()
    return True
