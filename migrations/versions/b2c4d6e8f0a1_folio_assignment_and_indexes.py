"""folio_assignment + índices compuestos (request_log, caf)

Revision ID: b2c4d6e8f0a1
Revises: f85b76e75638
Create Date: 2026-06-10 09:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c4d6e8f0a1'
down_revision: str | None = 'f85b76e75638'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'folio_assignment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.Integer(), nullable=False),
        sa.Column('folio', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', 'doc_type', 'folio'),
    )
    op.create_index(
        op.f('ix_folio_assignment_created_at'), 'folio_assignment', ['created_at'], unique=False
    )

    # Índices de consulta del access-log (portal por principal, panel por servicio).
    op.create_index(
        'ix_request_log_principal',
        'request_log',
        ['principal_type', 'principal_id', 'id'],
        unique=False,
    )
    op.create_index('ix_request_log_service', 'request_log', ['service_code', 'id'], unique=False)

    # CAF: reemplazar el índice por doc_type por el compuesto (customer_id, doc_type).
    op.drop_index(op.f('ix_caf_doc_type'), table_name='caf')
    op.create_index('ix_caf_customer_doctype', 'caf', ['customer_id', 'doc_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_caf_customer_doctype', table_name='caf')
    op.create_index(op.f('ix_caf_doc_type'), 'caf', ['doc_type'], unique=False)
    op.drop_index('ix_request_log_service', table_name='request_log')
    op.drop_index('ix_request_log_principal', table_name='request_log')
    op.drop_index(op.f('ix_folio_assignment_created_at'), table_name='folio_assignment')
    op.drop_table('folio_assignment')
