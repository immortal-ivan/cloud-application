"""roles viewer/operator/administrator and dotted permission codes (ЛР 21)

Revision ID: 0004
Revises: 0003
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSION_RENAMES = {
    "services:read": "services.read",
    "services:write": "services.write",
    "files:read": "files.read",
    "files:write": "files.write",
    "files:read_all": "files.read_all",
    "users:read": "users.manage",
}
ROLE_RENAMES = {"admin": "administrator", "user": "viewer"}


def _rename(table: str, column: str, mapping: dict[str, str]) -> None:
    for old, new in mapping.items():
        op.execute(f"UPDATE {table} SET {column} = '{new}' WHERE {column} = '{old}'")


def upgrade() -> None:
    # users:write объединяется с users.manage (право users:read уже переименовано в него)
    op.execute("DELETE FROM permissions WHERE code = 'users:write'")
    _rename("permissions", "code", PERMISSION_RENAMES)
    _rename("roles", "name", ROLE_RENAMES)
    # Дальше набор прав ролей и новые права (objects.*, roles.manage) выставляет scripts/seed.py


def downgrade() -> None:
    _rename("permissions", "code", {v: k for k, v in PERMISSION_RENAMES.items()})
    _rename("roles", "name", {v: k for k, v in ROLE_RENAMES.items()})
