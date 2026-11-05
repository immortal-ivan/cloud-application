"""Схемы ресурса /services (ЛР №5, №6): поля описаны и снабжены примерами для OpenAPI."""
from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Название облачного сервиса",
        examples=["Monitoring Service"],
    )
    type: str = Field(
        "application",
        description="Тип облачного сервиса: application, database или monitoring",
        examples=["monitoring"],
    )
    status: str = Field(
        "running",
        pattern="^(running|maintenance|stopped)$",
        description="Текущее состояние сервиса: running, maintenance или stopped",
        examples=["running"],
    )
    description: str = Field(
        "",
        max_length=500,
        description="Краткое описание сервиса",
        examples=["Сбор метрик и оповещения"],
    )


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор сервиса", examples=[1])
    name: str = Field(description="Название облачного сервиса", examples=["Web Service"])
    type: str = Field(description="Название типа сервиса (из таблицы service_types)", examples=["application"])
    status: str = Field(description="Текущее состояние сервиса", examples=["running"])
    description: str = Field(description="Краткое описание сервиса", examples=[""])
