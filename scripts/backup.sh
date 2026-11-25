#!/usr/bin/env bash
# Автоматизированное логическое резервное копирование PostgreSQL (ЛР 41).
# По умолчанию БД берётся из контейнера Docker Compose (сервис db).
# BACKUP_MODE=local – PostgreSQL доступен напрямую (PGHOST/PGPORT/PGUSER/PGPASSWORD).
set -Eeuo pipefail
umask 077

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

MODE="${BACKUP_MODE:-docker}"

# Выполнение команды PostgreSQL: в контейнере db или локально.
db_exec() {
  if [ "$MODE" = "local" ]; then
    "$@"
  else
    docker compose exec -T db "$@"
  fi
}

# Параметры подключения
if [ "$MODE" = "local" ]; then
  DB_USER="${PGUSER:-postgres}"
  DB_NAME="${DB_NAME:-cloud_application}"
else
  DB_USER=$(docker compose exec -T db printenv POSTGRES_USER)
  DB_NAME=$(docker compose exec -T db printenv POSTGRES_DB)
fi

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/cloudapp_${DATE}.dump"
TEMP_FILE="${BACKUP_FILE}.tmp"

# Временный файл удаляется, если сценарий завершился с ошибкой
trap 'rm -f "$TEMP_FILE"' EXIT

echo "Starting database backup..."
db_exec pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "$TEMP_FILE"

# Проверка размера и читаемости архива до сохранения под итоговым именем
test -s "$TEMP_FILE"
db_exec pg_restore --list < "$TEMP_FILE" > /dev/null

mv "$TEMP_FILE" "$BACKUP_FILE"
sha256sum "$BACKUP_FILE" > "${BACKUP_FILE}.sha256"

echo "Backup completed successfully"
echo "File: $BACKUP_FILE"
