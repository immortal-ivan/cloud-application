"""Настройки приложения.

Значения читаются из переменных окружения, файла .env и каталога secrets/
(каждый файл каталога = одно секретное значение, имя файла = имя настройки).
"""
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent.parent

# Основные параметры приложения (ЛР №2): название и версия вынесены из main.py
APP_NAME = "Cloud Application"
APP_VERSION = "1.0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        secrets_dir=BASE_DIR / "secrets",
        extra="ignore",
    )

    app_name: str = APP_NAME
    app_version: str = APP_VERSION

    # База данных PostgreSQL. Пароль берётся из secrets/db_password.
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cloud_app"
    db_user: str = "cloud_user"
    db_password: str = Field(default="")
    # Полный адрес БД имеет приоритет (например, для тестов на SQLite).
    database_url: str | None = None

    # Авторизация
    token_ttl_minutes: int = 60

    # Файловое хранилище
    storage_dir: Path = BASE_DIR / "storage"
    max_upload_mb: int = 5
    # Объектное хранилище (ЛР №18): каталог физических объектов и предельный размер файла
    storage_path: str = "storage/objects"
    max_upload_size: int = 5 * 1024 * 1024

    # Адрес прослушивания. В контейнере задаётся APP_HOST=0.0.0.0 и APP_PORT=8000;
    # прежние имена HOST/PORT по-прежнему поддерживаются.
    host: str = Field(default="127.0.0.1", validation_alias=AliasChoices("app_host", "host"))
    port: int = Field(default=8443, validation_alias=AliasChoices("app_port", "port"))

    # Notification Service (ЛР №29). В Docker Compose: http://notification:9000
    notification_service_url: str = "http://127.0.0.1:9000"
    # Устойчивость вызова (ЛР №30): тайм-аут одной попытки, число попыток, начальная задержка
    notification_timeout_seconds: float = 2.0
    notification_max_attempts: int = 3
    notification_retry_delay_seconds: float = 0.5

    # HTTPS
    https_enabled: bool = True
    ssl_certfile: Path = BASE_DIR / "certs" / "localhost.pem"
    ssl_keyfile: Path = BASE_DIR / "certs" / "localhost-key.pem"

    @model_validator(mode="after")
    def _require_secrets(self) -> "Settings":
        """Без обязательного секрета приложение не запускается (слабых значений по умолчанию нет)."""
        if not self.database_url and not self.db_password:
            raise ValueError("Не задан секрет db_password (файл secrets/db_password)")
        return self

    @property
    def sqlalchemy_url_str(self) -> str:
        """Адрес БД строкой, с паролем (для Alembic)."""
        url = self.sqlalchemy_url
        return url if isinstance(url, str) else url.render_as_string(hide_password=False)

    @property
    def sqlalchemy_url(self) -> str | URL:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg2",
            username=self.db_user,
            password=self.db_password or None,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
