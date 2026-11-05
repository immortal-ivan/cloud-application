# Сетевые параметры запуска (ЛР №3)

Адрес и порт сервера задаются при запуске, исходный код `app/main.py` при этом не меняется.

| Запуск | Результат |
|---|---|
| `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | доступен только на этом компьютере, порт 8000 |
| `python -m uvicorn app.main:app --host 127.0.0.1 --port 8080` | то же, порт 8080 |
| `python -m uvicorn app.main:app --host 127.0.0.1 --port 9000` | самостоятельное задание, порт 9000 |
| `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` | принимает соединения через все сетевые интерфейсы |

Через `python run.py` те же параметры задаются переменными `APP_HOST` и `APP_PORT` (или `HOST` и `PORT`).

Проверка в Windows PowerShell: `hostname`, `ipconfig`, `ping 127.0.0.1`,
`Test-NetConnection 127.0.0.1 -Port 8000`, `netstat -ano | findstr :8000`.
