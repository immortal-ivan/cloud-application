# Cloud Application

Учебный проект по дисциплине «Управление работами и разработка ПО облачных систем».

## Структура проекта

```
cloud-app/
├── app/
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Установка и запуск

### ЛР №1 — Подготовка среды

```bash
# 1. Создать виртуальное окружение
python -m venv .venv

# 2. Активировать (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Если ошибка политики выполнения:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Установить зависимости
pip install fastapi uvicorn

# 4. Запустить приложение
python -m uvicorn app.main:app --reload

# 5. Сохранить зависимости
pip freeze > requirements.txt
```

### ЛР №2 — Проверка эндпоинтов

Открой в браузере после запуска сервера:

| Адрес | Описание |
|---|---|
| http://127.0.0.1:8000 | Основная информация |
| http://127.0.0.1:8000/status | Состояние приложения |
| http://127.0.0.1:8000/about | Информация о стеке |
| http://127.0.0.1:8000/course | Информация о дисциплине |

### ЛР №3 — Сетевые параметры

```bash
# Запуск с явным адресом и портом
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Запуск на другом порту
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload

# Запуск на всех интерфейсах
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Запуск на порту 9000 (самостоятельное задание)
python -m uvicorn app.main:app --host 127.0.0.1 --port 9000 --reload
```

### Команды для ЛР №3 (второй терминал)

```bash
# Определить имя компьютера
hostname

# Определить IPv4 адрес
ipconfig

# Проверить loopback
ping 127.0.0.1

# Проверить доступность порта
Test-NetConnection 127.0.0.1 -Port 8000
Test-NetConnection 127.0.0.1 -Port 8080
Test-NetConnection 127.0.0.1 -Port 9000

# Найти прослушиваемый порт
netstat -ano | findstr :8000
netstat -ano | findstr :8080
netstat -ano | findstr :9000
```
