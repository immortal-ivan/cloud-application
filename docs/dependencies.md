# Зависимости Cloud Application

## Среда выполнения

Python: 3.13.16

## Прямые зависимости

- FastAPI - REST API
- Uvicorn - ASGI-сервер
- SQLAlchemy - ORM и доступ к БД
- Alembic - миграции
- psycopg2-binary - драйвер PostgreSQL
- pydantic-settings - конфигурация
- python-multipart - загрузка файлов
- pwdlib - работа с хешами паролей

## Файлы зависимостей

- requirements-direct.txt - прямые зависимости без версий (что выбрал разработчик)
- requirements.txt - зафиксированное проверенное окружение с точными версиями

## Установка

python -m pip install -r requirements.txt

## Проверка

python -m pip check

## Правила изменения зависимостей

Новая внешняя библиотека добавляется только тогда, когда она действительно необходима
функциональности проекта. После изменения набора пакетов необходимо:

1. добавить библиотеку в requirements-direct.txt;
2. обновить requirements.txt командой pip freeze;
3. выполнить pip check;
4. проверить установку в чистом окружении (.venv-check) и запуск приложения;
5. обновить этот документ и зафиксировать изменения в Git.
