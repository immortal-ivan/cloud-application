"""service types (ЛР 15)

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.execute(
        "INSERT INTO service_types (name, description) VALUES "
        "('application', 'Прикладной сервис'), ('database', 'Сервис базы данных'), "
        "('monitoring', 'Сервис мониторинга')"
    )
    # Существующие услуги получают тип application, затем столбец становится обязательным
    op.add_column("services", sa.Column("type_id", sa.Integer(), nullable=True))
    op.execute("UPDATE services SET type_id = (SELECT id FROM service_types WHERE name = 'application')")
    op.alter_column("services", "type_id", nullable=False)
    op.create_foreign_key("fk_services_type_id_service_types", "services", "service_types", ["type_id"], ["id"])
    # Состояния приводятся к running / maintenance / stopped
    op.execute("UPDATE services SET status = 'running' WHERE status = 'active'")
    op.execute("UPDATE services SET status = 'stopped' WHERE status = 'disabled'")


def downgrade() -> None:
    op.execute("UPDATE services SET status = 'active' WHERE status = 'running'")
    op.execute("UPDATE services SET status = 'disabled' WHERE status IN ('stopped', 'maintenance')")
    op.drop_constraint("fk_services_type_id_service_types", "services", type_="foreignkey")
    op.drop_column("services", "type_id")
    op.drop_table("service_types")
