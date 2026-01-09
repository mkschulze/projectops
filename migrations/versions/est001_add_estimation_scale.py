"""Add estimation scale fields to Project

Revision ID: est001
Revises: mt001_add_multi_tenancy
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'est001'
down_revision = None  # Will be auto-detected
branch_labels = None
depends_on = None


def upgrade():
    # Add estimation_scale column
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('estimation_scale', sa.String(20), nullable=True, server_default='fibonacci'))
        batch_op.add_column(sa.Column('estimation_values', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('estimation_values')
        batch_op.drop_column('estimation_scale')
