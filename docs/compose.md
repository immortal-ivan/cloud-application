# ЛР №28. Cloud Application + PostgreSQL в Docker Compose

Сервисы `compose.yaml`:

| Сервис | Образ | Назначение |
|---|---|---|
| `db` | `postgres:18` | PostgreSQL, данные в volume `postgres_data`, порт на хост не публикуется |
| `migrate` | `cloud-application:0.2` | одноразовый: `alembic upgrade head` + `python -m scripts.seed` (права, роли, учебные пользователи) |
| `app` | `cloud-application:0.2` | FastAPI, `127.0.0.1:8080 -> 8000`, `DB_HOST=db`, файлы в volume `app_storage` |

Особенности проекта по сравнению с методичкой:

- Секрет один - `secrets/db_password`. Он передаётся PostgreSQL через
  `POSTGRES_PASSWORD_FILE=/run/secrets/db_password`, а приложению - как файл
  `/app/secrets/db_password`. Пароля в `compose.yaml` нет.
- Миграция `0001_initial_schema` создаёт все таблицы с нуля, поэтому
  `docker/postgres/01_base_schema.sql` не создаёт таблиц (иначе Alembic упадёт
  на `relation already exists`).
- Ролевая модель проекта: роли `viewer`, `operator`, `administrator`, права вида `services.write`.
  Её создаёт `scripts/seed.py`, поэтому скрипт добавлен в образ.
- Пользователь `compose_user` создаётся самостоятельной регистрацией `POST /auth/register`
  (роль viewer) либо администратором через `POST /users`.
- Дополнительное задание выполнено: в образ добавлен каталог `/app/storage`
  с владельцем `appuser`, к нему подключён volume `app_storage`. Из-за
  изменения Dockerfile собирается версия `0.2`.

## Запуск

```powershell
docker build -t cloud-application:0.2 .
docker stop cloud-application-container; docker rm cloud-application-container   # если остался после ЛР №27
docker compose config -q
docker compose up -d
docker compose ps -a        # db healthy, app Up, migrate Exited (0)
docker compose logs migrate
```

## Проверки

```powershell
curl.exe http://127.0.0.1:8080/status     # "database":"ok"
docker compose exec app python -c "import socket; print(socket.gethostbyname('db'))"
docker compose exec app python -c "from app.config import settings; print(settings.db_host)"   # db
docker compose exec db psql -U postgres -d cloud_application -c "\dt"
docker compose exec db psql -U postgres -d cloud_application -c "SELECT * FROM alembic_version;"   # 0004
docker compose exec db psql -U postgres -d cloud_application -c "SELECT name FROM roles ORDER BY id;"   # viewer, operator, administrator, content_manager
```

Пользователь через API (Swagger `http://127.0.0.1:8080/docs`): вход `admin` / `Admin#2026`,
`POST /users` с телом
`{"username": "compose_user", "email": "compose@cloud.local", "password": "CloudCompose123"}`,
затем вход `compose_user`, `GET /auth/me`, `GET /services`.

## Сохранение данных

```powershell
docker compose exec db psql -U postgres -d cloud_application -c "INSERT INTO services (name, description, status, created_at) VALUES ('Compose Test Service', 'test', 'active', now());"
docker compose down          # контейнеры и сеть удалены
docker volume ls             # ..._postgres_data на месте
docker compose up -d
docker compose exec db psql -U postgres -d cloud_application -c "SELECT id, name, status FROM services ORDER BY id;"
```

`docker compose down -v` удаляет и volumes - выполнять только после всех проверок.
