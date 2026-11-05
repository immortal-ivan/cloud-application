FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt

RUN useradd \
    --create-home \
    --shell /usr/sbin/nologin \
    appuser

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser migrations ./migrations
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser run.py ./
# Начальные данные (роли, права, учебные пользователи) для сервиса migrate
COPY --chown=appuser:appuser scripts/__init__.py scripts/seed.py ./scripts/

# Каталог файлового хранилища, доступный appuser (подключается volume app_storage)
RUN mkdir -p /app/storage \
    && chown -R appuser:appuser /app/storage

USER appuser

EXPOSE 8000

LABEL org.opencontainers.image.title="Cloud Application"
LABEL org.opencontainers.image.version="0.3"

CMD ["python", "run.py"]
