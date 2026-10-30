"""Настройки приложения.

Значения читаются из переменных окружения, файла .env и каталога secrets/
(каждый файл каталога = одно секретное значение, имя файла = имя настройки).
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        secrets_dir=BASE_DIR / "secrets",
        extra="ignore",
    )

    app_name: str = "Cloud Application"
    app_version: str = "0.1.0"

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

    # HTTPS
    host: str = "127.0.0.1"
    port: int = 8443
    https_enabled: bool = True
    ssl_certfile: Path = BASE_DIR / "certs" / "localhost.pem"
    ssl_keyfile: Path = BASE_DIR / "certs" / "localhost-key.pem"

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
