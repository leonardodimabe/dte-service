"""machine_key: unifica a soft delete (deleted_at, elimina is_active)

Revision ID: f6a8b0d2c4e5
Revises: e5f7a9c1b3d4
Create Date: 2026-06-16 13:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f6a8b0d2c4e5'
down_revision: str | None = 'e5f7a9c1b3d4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('machine_key', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    # Preserva el estado: las claves revocadas (is_active=false) pasan a archivadas.
    op.execute(
        "UPDATE machine_key SET deleted_at = CURRENT_TIMESTAMP WHERE is_active = false"
    )
    op.drop_column('machine_key', 'is_active')


def downgrade() -> None:
    op.add_column(
        'machine_key',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.execute("UPDATE machine_key SET is_active = (deleted_at IS NULL)")
    op.drop_column('machine_key', 'deleted_at')
