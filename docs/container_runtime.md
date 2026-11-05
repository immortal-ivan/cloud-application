# ЛР №27. Запуск Cloud Application в контейнере

Образ `cloud-application:0.1` (ЛР №26) запускается как контейнер. Конфигурация
передаётся при запуске, образ не меняется.

## Изменения в проекте

- `app/config.py`: адрес и порт можно задавать через `APP_HOST` / `APP_PORT`
  (прежние `HOST` / `PORT` тоже работают, `APP_*` имеют приоритет).
- `app/config.py`: без секрета `db_password` приложение отказывается запускаться
  (исключение - явный `DATABASE_URL`, например SQLite для разработки).
- `app/routers/status.py`: `/status` отвечает 200 даже без доступной БД и
  показывает `"database": "unavailable"`. Это позволяет проверить контейнер
  до появления PostgreSQL-сервиса (ЛР №28).

После изменения кода образ пересобирается тем же тегом:

```powershell
docker build -t cloud-application:0.1 .
```

## Секреты проекта

В проекте используется один runtime-секрет: `secrets/db_password` (пароль БД).
Токены доступа случайные и хранятся в БД в виде SHA-256, отдельный `auth_secret`
проекту не нужен.

```powershell
Test-Path .\secrets\db_password   # True
```

## Запуск

```powershell
$projectPath = (Get-Location).Path

docker run -d `
    --name cloud-application-container `
    -p 127.0.0.1:8080:8000 `
    --env-file .env `
    -e APP_HOST=0.0.0.0 `
    -e APP_PORT=8000 `
    -e HTTPS_ENABLED=false `
    --mount "type=bind,source=$projectPath\secrets,target=/app/secrets,readonly" `
    cloud-application:0.1
```

| Параметр | Назначение |
|---|---|
| `-d` | фоновый режим |
| `--name` | понятное имя контейнера |
| `-p 127.0.0.1:8080:8000` | порт 8080 компьютера -> порт 8000 контейнера, доступ только локально |
| `--env-file .env` | обычная конфигурация |
| `APP_HOST=0.0.0.0` | Uvicorn слушает сетевые интерфейсы контейнера, а не только его loopback |
| `APP_PORT=8000` | внутренний порт приложения (совпадает с `EXPOSE 8000`) |
| `HTTPS_ENABLED=false` | в этой ЛР исследуется жизненный цикл контейнера, без TLS |
| `--mount ...,readonly` | каталог секретов подключается только для чтения, в образ не попадает |

## Проверки

```powershell
docker ps
docker port cloud-application-container          # 8000/tcp -> 127.0.0.1:8080
curl.exe http://127.0.0.1:8080/status            # {"status":"ok",...,"database":"unavailable"}
# браузер: http://127.0.0.1:8080/docs

docker logs --tail 20 cloud-application-container
docker logs -f cloud-application-container       # Ctrl+C прекращает только просмотр

docker exec cloud-application-container whoami   # appuser
docker exec cloud-application-container pwd      # /app
docker exec cloud-application-container ls -la
docker exec cloud-application-container python --version
docker exec cloud-application-container sh -c 'echo $APP_HOST'       # 0.0.0.0
docker exec cloud-application-container sh -c 'echo $APP_PORT'       # 8000
docker exec cloud-application-container sh -c 'echo $HTTPS_ENABLED'  # false
docker exec cloud-application-container sh -c 'test -f /app/secrets/db_password && echo DB_SECRET_EXISTS'
docker inspect cloud-application-container --format '{{json .Mounts}}'   # "RW":false
```

`"database": "unavailable"` на этом этапе ожидаем: в `.env` указан `DB_HOST=localhost`,
а внутри контейнера `localhost` - это сам контейнер. PostgreSQL подключается в ЛР №28.

## Жизненный цикл

```powershell
docker stop cloud-application-container
docker ps -a                                    # Exited
curl.exe http://127.0.0.1:8080/status           # нет ответа
docker start cloud-application-container       # параметры запуска сохранены
docker restart cloud-application-container
docker inspect cloud-application-container --format '{{.State.Status}}'   # running / exited
docker stop cloud-application-container
docker rm cloud-application-container
docker image ls cloud-application               # образ 0.1 на месте
```

## Самостоятельная работа

Второй экземпляр того же образа - тот же внутренний порт 8000, другой host port 8081:

```powershell
docker run -d --name cloud-application-second -p 127.0.0.1:8081:8000 `
    --env-file .env -e APP_HOST=0.0.0.0 -e APP_PORT=8000 -e HTTPS_ENABLED=false `
    --mount "type=bind,source=$projectPath\secrets,target=/app/secrets,readonly" `
    cloud-application:0.1
```

Третий контейнер с занятым `127.0.0.1:8080:8000` не стартует: `port is already allocated`.

| Проверка | Основной контейнер | Второй контейнер |
|---|---|---|
| Имя | cloud-application-container | cloud-application-second |
| Образ | cloud-application:0.1 | cloud-application:0.1 |
| Внутренний порт | 8000 | 8000 |
| Host port | 8080 | 8081 |
| /status доступен | да | да |
| /docs доступен | да | да |
| Пользователь appuser | да | да |
| Секреты подключены | да | да |
| Состояние Running | да | да |

Эксперимент без секретов:

```powershell
docker stop cloud-application-second; docker rm cloud-application-second
docker run -d --name cloud-no-secrets -p 127.0.0.1:8081:8000 `
    --env-file .env -e APP_HOST=0.0.0.0 -e APP_PORT=8000 -e HTTPS_ENABLED=false `
    cloud-application:0.1
docker ps -a                 # cloud-no-secrets: Exited (1)
docker logs cloud-no-secrets # ValidationError: Не задан секрет db_password
docker rm cloud-no-secrets
```

Приложение отказывается запускаться без обязательного секрета - это правильное поведение.
Образ при этом не пересобирался: менялись только имя, порт, переменные среды и mounts.
