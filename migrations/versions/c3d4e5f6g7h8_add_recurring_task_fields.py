"""Add recurring task fields to task_preset and task

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade():
    # Add recurrence fields to task_preset
    with op.batch_alter_table('task_preset', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_recurring', sa.Boolean(), nullable=True, default=False))
        batch_op.add_column(sa.Column('recurrence_frequency', sa.String(length=20), nullable=True, default='none'))
        batch_op.add_column(sa.Column('recurrence_rrule', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('recurrence_day_offset', sa.Integer(), nullable=True, default=0))
        batch_op.add_column(sa.Column('recurrence_end_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('last_generated_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('default_owner_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('default_entity_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_preset_owner', 'user', ['default_owner_id'], ['id'])
        batch_op.create_foreign_key('fk_preset_entity', 'entity', ['default_entity_id'], ['id'])
    
    # Add recurring task fields to task
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preset_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_recurring_instance', sa.Boolean(), nullable=True, default=False))
        batch_op.create_index('ix_task_preset_id', ['preset_id'])
        batch_op.create_foreign_key('fk_task_preset', 'task_preset', ['preset_id'], ['id'])
    
    # Set defaults for existing records
    op.execute("UPDATE task_preset SET is_recurring = 0 WHERE is_recurring IS NULL")
    op.execute("UPDATE task_preset SET recurrence_frequency = 'none' WHERE recurrence_frequency IS NULL")
    op.execute("UPDATE task_preset SET recurrence_day_offset = 0 WHERE recurrence_day_offset IS NULL")
    op.execute("UPDATE task SET is_recurring_instance = 0 WHERE is_recurring_instance IS NULL")


def downgrade():
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_constraint('fk_task_preset', type_='foreignkey')
        batch_op.drop_index('ix_task_preset_id')
        batch_op.drop_column('is_recurring_instance')
        batch_op.drop_column('preset_id')
    
    with op.batch_alter_table('task_preset', schema=None) as batch_op:
        batch_op.drop_constraint('fk_preset_entity', type_='foreignkey')
        batch_op.drop_constraint('fk_preset_owner', type_='foreignkey')
        batch_op.drop_column('default_entity_id')
        batch_op.drop_column('default_owner_id')
        batch_op.drop_column('last_generated_date')
        batch_op.drop_column('recurrence_end_date')
        batch_op.drop_column('recurrence_day_offset')
        batch_op.drop_column('recurrence_rrule')
        batch_op.drop_column('recurrence_frequency')
        batch_op.drop_column('is_recurring')
