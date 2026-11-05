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

Учебные пользователи (роли и права создаёт `python -m scripts.seed`): `admin` и `student03` / `Admin#2026`, `Student#2026` - administrator; `student01` - viewer; `student02` - operator (пароль учебных студентов `Student#2026`).

## Проверка

`python -m scripts.smoke_test` (приложение должно быть запущено) - 40 контрольных проверок: `/`, `/status`, `/about`, `/course`, вход, `/auth/me`, 401 и 403, услуги, `/objects` (в том числе лимит 5 МБ), смена роли без нового токена, завершение сеанса.

## Основные маршруты

| Метод и путь | Право | Назначение |
|---|---|---|
| `GET /`, `GET /status`, `GET /about`, `GET /course` | - | сведения о приложении, состояние приложения и БД |
| `POST /auth/register`, `POST /auth/login` | - | регистрация (роль viewer), вход, выдаёт Bearer-токен |
| `GET /auth/me`, `POST /auth/logout` | токен | текущий пользователь, выход |
| `GET/DELETE /auth/session/{token}` | - | проверка и завершение сеанса |
| `GET /services`, `GET /services/{id}` | services.read | каталог сервисов (фильтр `?status=`) |
| `POST/PUT/DELETE /services` | services.write | управление сервисами |
| `GET /objects`, `GET /objects/{id}`, `GET /objects/{id}/download` | objects.read | объектное хранилище |
| `POST /objects`, `DELETE /objects/{id}` | objects.write | загрузка (до 5 МБ) и удаление |
| `GET /access/roles`, `PUT /access/users/{id}/role` | roles.manage | роли и назначение ролей |
| `GET /access/users/{id}` | users.manage | сведения о пользователе |
| `GET /access/summary` | users.manage или roles.manage | учебная сводка (`require_any_permission`) |
| `GET/POST /users` | users.manage | учётные записи |
| `POST /files`, `GET /files`, `GET /files/{id}/download` | files.write / files.read | личные файлы пользователя |

Роли: viewer (чтение), operator (чтение и изменение services и objects), administrator (все разрешения), content_manager (objects.read/write и services.read).

## Структура

- `app/` - исходный код (`config.py`, `security.py`, `crypto.py`, `data/` - подключение и ORM-модели, `services/` - бизнес-логика, `schemas/`, `routers/`)
- `migrations/`, `alembic.ini` - миграции схемы БД
- `run.py` - запуск (HTTPS, если есть `certs/localhost.pem`)
- `scripts/` - начальные данные, проверка, подготовка Windows
- `.env`, `secrets/`, `certs/*.pem`, `storage/` - локальные данные, в Git не попадают

## Docker (ЛР №26–30)

- `Dockerfile` - образ приложения (`docker build -t cloud-application:0.3 .`)
- `compose.yaml` - система `app` + `db` (PostgreSQL 18) + `migrate` + `notification`:
  `docker compose up -d`, затем `http://127.0.0.1:8080/docs`
- `POST /integration/notifications` - вызов внутреннего Notification Service
  (тайм-аут, retry, ответы 502/503/504)
- `docs/container_runtime.md`, `docs/compose.md` - команды лабораторных работ
- `отчеты/` - отчёты по лабораторным работам (№2, 3, 6, 15, 18, 21, 26–30)
