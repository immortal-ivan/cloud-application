-- Скрипт начальной инициализации PostgreSQL (выполняется только для пустого volume).
--
-- В методичке ЛР №28 здесь воссоздаются таблицы service_types и services из ЛР №14,
-- потому что там первая миграция Alembic была baseline существующей схемы.
-- В этом проекте первая миграция 0001_initial_schema сама создаёт все таблицы
-- с нуля (permissions, roles, role_permissions, users, services, access_tokens,
-- stored_files). Если создать services здесь, alembic upgrade head упадёт
-- с ошибкой "relation already exists". Поэтому схему создаёт только Alembic,
-- а этот файл лишь фиксирует факт инициализации.

COMMENT ON DATABASE cloud_application IS 'Cloud Application (Docker Compose)';
