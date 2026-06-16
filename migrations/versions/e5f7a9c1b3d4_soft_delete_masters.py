"""soft delete en maestros (customer, app_user): deleted_at

Revision ID: e5f7a9c1b3d4
Revises: d4e6f8a0b2c3
Create Date: 2026-06-16 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e5f7a9c1b3d4'
down_revision: str | None = 'd4e6f8a0b2c3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('customer', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('app_user', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('app_user', 'deleted_at')
    op.drop_column('customer', 'deleted_at')
