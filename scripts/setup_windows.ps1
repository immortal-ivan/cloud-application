# Первичная подготовка Cloud Application на Windows.
# Запуск (из корня проекта):   powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
# Ключ -Sqlite: использовать SQLite вместо PostgreSQL (если PostgreSQL недоступен).
param([switch]$Sqlite)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host 'Python не найден в PATH.' -ForegroundColor Red; exit 1
}
python --version

# 1. Рабочее виртуальное окружение с прямыми зависимостями (исходное состояние перед ЛР №25)
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]" sqlalchemy alembic psycopg2-binary pydantic-settings python-multipart "pwdlib[argon2]"
if ($LASTEXITCODE -ne 0) { Write-Host 'Установка пакетов не удалась' -ForegroundColor Red; exit 1 }

# 2. Локальная конфигурация и секреты (в Git не попадают)
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
New-Item -ItemType Directory -Force secrets, storage | Out-Null
if (-not (Test-Path secrets\db_password)) {
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) 'secrets\db_password'), 'cloud_pass_2026')
}
if ($Sqlite) {
    $lines = @(Get-Content .env | Where-Object { $_ -notmatch '^DATABASE_URL=' })
    $lines += 'DATABASE_URL=sqlite:///./cloud_app.db'
    [System.IO.File]::WriteAllLines((Join-Path (Get-Location) '.env'), $lines)
    Write-Host 'Режим SQLite: база cloud_app.db в корне проекта' -ForegroundColor Yellow
}

# 3. Сертификат HTTPS
if (-not (Test-Path certs\localhost.pem)) { & "$PSScriptRoot\make_cert.ps1" }

# 4. Миграции и начальные данные
.\.venv\Scripts\python.exe -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Миграции не применены. Для PostgreSQL выполните scripts/create_db.sql в pgAdmin и проверьте, что сервер запущен; либо запустите скрипт с ключом -Sqlite.' -ForegroundColor Red
    exit 1
}
.\.venv\Scripts\python.exe -m scripts.seed

Write-Host ''
Write-Host 'Готово. Активируйте окружение:  .venv\Scripts\Activate.ps1   затем:  python run.py' -ForegroundColor Green
Write-Host 'Адрес: https://localhost:8443/docs   Пользователи: admin / Admin#2026,  student / Student#2026' -ForegroundColor Green
