# Cloud Application

Учебный облачный сервис: REST API на FastAPI с PostgreSQL (SQLAlchemy, миграции Alembic), аутентификацией по Bearer-токену, ролями и правами, загрузкой файлов, хранением паролей в Argon2 (pwdlib), конфигурацией через `.env` и `secrets/`, поддержкой HTTPS.

## Быстрый старт (Windows, PowerShell)

1. PostgreSQL: в pgAdmin выполните `scripts/create_db.sql` (создаёт пользователя `cloud_user` и базу `cloud_app`).
   Нет PostgreSQL — используйте ключ `-Sqlite` (шаг 2).
2. Подготовка проекта (окружение `.venv`, `.env`, `secrets/`, сертификат HTTPS, миграции, начальные данные):
   `powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1`
   (или с SQLite: `... setup_windows.ps1 -Sqlite`)
3. Запуск: `.venv\Scripts\Activate.ps1`, затем `python run.py`
4. Откройте `https://localhost:8443/docs` (браузер предупредит о самоподписанном сертификате, это нормально для учебной среды).

Учебные пользователи: `admin` / `Admin#2026` (все права), `student` / `Student#2026` (роль user).

## Проверка

`python -m scripts.smoke_test` (приложение должно быть запущено) - 20 контрольных проверок: `/status`, вход, `/auth/me`, права (403), услуги, загрузка и скачивание файла, выход.

## Основные маршруты

| Метод и путь | Право | Назначение |
|---|---|---|
| `GET /status` | - | состояние приложения и БД |
| `POST /auth/login` | - | вход, выдаёт Bearer-токен |
| `GET /auth/me`, `POST /auth/logout` | токен | текущий пользователь, выход |
| `GET/POST /users` | users:read / users:write | пользователи |
| `GET /services`, `GET /services/{id}` | services:read | каталог услуг |
| `POST/PUT/DELETE /services` | services:write | управление услугами |
| `POST /files`, `GET /files`, `GET /files/{id}/download` | files:write / files:read | файлы пользователя |

## Структура

- `app/` - исходный код (`config.py`, `database.py`, `models.py`, `security.py`, `deps.py`, `routers/`)
- `migrations/`, `alembic.ini` - миграции схемы БД
- `run.py` - запуск (HTTPS, если есть `certs/localhost.pem`)
- `scripts/` - начальные данные, проверка, подготовка Windows
- `.env`, `secrets/`, `certs/*.pem`, `storage/` - локальные данные, в Git не попадают
