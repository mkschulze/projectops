"""Add user entity permissions table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-30 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_entity permissions table
    op.create_table('user_entity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('access_level', sa.String(length=20), nullable=True, default='view'),
        sa.Column('inherit_to_children', sa.Boolean(), nullable=True, default=True),
        sa.Column('granted_by_id', sa.Integer(), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ),
        sa.ForeignKeyConstraint(['granted_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'entity_id', name='unique_user_entity')
    )
    
    # Create indexes for faster lookups
    op.create_index('ix_user_entity_user_id', 'user_entity', ['user_id'])
    op.create_index('ix_user_entity_entity_id', 'user_entity', ['entity_id'])


def downgrade():
    op.drop_index('ix_user_entity_entity_id', 'user_entity')
    op.drop_index('ix_user_entity_user_id', 'user_entity')
    op.drop_table('user_entity')
