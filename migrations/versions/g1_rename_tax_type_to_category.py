"""Rename tax_type to task_category for abstraction

Revision ID: g1_rename_tax_type_to_category
Revises: mt001_add_multi_tenancy
Create Date: 2026-01-03

This migration abstracts TaxType to the more general TaskCategory model,
allowing for both tax-related and non-tax categories while maintaining
backward compatibility.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'g1_rename_tax_type_to_category'
down_revision = 'mt001_add_multi_tenancy'
branch_labels = None
depends_on = None


def upgrade():
    # Check if tables exist
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # If task_category already exists, skip renaming
    if 'task_category' not in tables and 'tax_type' in tables:
        # Rename tax_type table to task_category
        op.rename_table('tax_type', 'task_category')
    
    # Add new columns to task_category table if they don't exist
    if 'task_category' in tables:
        columns = [col['name'] for col in inspector.get_columns('task_category')]
        with op.batch_alter_table('task_category', schema=None) as batch_op:
            if 'color' not in columns:
                batch_op.add_column(sa.Column('color', sa.String(7), nullable=True, server_default='#6c757d'))
            if 'icon' not in columns:
                batch_op.add_column(sa.Column('icon', sa.String(50), nullable=True, server_default='bi-folder'))
    
    # Rename foreign key column in task_template if needed
    if 'task_template' in tables:
        columns = [col['name'] for col in inspector.get_columns('task_template')]
        if 'tax_type_id' in columns and 'category_id' not in columns:
            with op.batch_alter_table('task_template', schema=None) as batch_op:
                batch_op.alter_column('tax_type_id', new_column_name='category_id')


def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Rename foreign key column back
    if 'task_template' in tables:
        columns = [col['name'] for col in inspector.get_columns('task_template')]
        if 'category_id' in columns:
            with op.batch_alter_table('task_template', schema=None) as batch_op:
                batch_op.alter_column('category_id', new_column_name='tax_type_id')
    
    # Remove new columns
    if 'task_category' in tables:
        with op.batch_alter_table('task_category', schema=None) as batch_op:
            batch_op.drop_column('icon')
            batch_op.drop_column('color')
    
    # Rename table back
    if 'task_category' in tables:
        op.rename_table('task_category', 'tax_type')
