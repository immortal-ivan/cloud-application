"""Запуск Cloud Application. HTTPS включается, если есть сертификаты в certs/."""
import uvicorn

from app.config import settings


def main() -> None:
    kwargs: dict = {"host": settings.host, "port": settings.port}

    if settings.https_enabled and settings.ssl_certfile.exists() and settings.ssl_keyfile.exists():
        kwargs.update(ssl_certfile=str(settings.ssl_certfile), ssl_keyfile=str(settings.ssl_keyfile))
        print(f"HTTPS: https://localhost:{settings.port}")
    else:
        print(f"HTTP (сертификаты не найдены или HTTPS выключен): http://localhost:{settings.port}")

    uvicorn.run("app.main:app", **kwargs)


if __name__ == "__main__":
    main()
