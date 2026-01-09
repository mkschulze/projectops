"""Add custom fields for presets

Revision ID: c4d5e6f7g8h9
Revises: b4301e4eea63
Create Date: 2025-12-31 13:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c4d5e6f7g8h9'
down_revision = 'b4301e4eea63'
branch_labels = None
depends_on = None


def upgrade():
    # Create preset_custom_field table
    op.create_table('preset_custom_field',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('preset_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('label_de', sa.String(length=200), nullable=False),
        sa.Column('label_en', sa.String(length=200), nullable=True),
        sa.Column('field_type', sa.String(length=20), nullable=False, server_default='text'),
        sa.Column('is_required', sa.Boolean(), default=False),
        sa.Column('placeholder_de', sa.String(length=200), nullable=True),
        sa.Column('placeholder_en', sa.String(length=200), nullable=True),
        sa.Column('default_value', sa.String(length=500), nullable=True),
        sa.Column('options', sa.Text(), nullable=True),
        sa.Column('validation_regex', sa.String(length=200), nullable=True),
        sa.Column('help_text_de', sa.Text(), nullable=True),
        sa.Column('help_text_en', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('condition_field', sa.String(length=100), nullable=True),
        sa.Column('condition_operator', sa.String(length=20), nullable=True),
        sa.Column('condition_value', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['preset_id'], ['task_preset.id'], name='fk_custom_field_preset'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create task_custom_field_value table
    op.create_table('task_custom_field_value',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], name='fk_field_value_task'),
        sa.ForeignKeyConstraint(['field_id'], ['preset_custom_field.id'], name='fk_field_value_field'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id', 'field_id', name='unique_task_field_value')
    )


def downgrade():
    op.drop_table('task_custom_field_value')
    op.drop_table('preset_custom_field')
