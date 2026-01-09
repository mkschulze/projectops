"""Add multi-tenancy support

Revision ID: mt001_add_multi_tenancy
Revises: pm6_add_issue_details_tables
Create Date: 2026-01-03

This migration adds:
1. Tenant table for multi-tenancy
2. TenantMembership table for user-tenant assignment
3. TenantApiKey table for API integrations
4. tenant_id foreign keys to all tenant-aware tables
5. is_superadmin and current_tenant_id to User table
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'mt001_add_multi_tenancy'
down_revision = '1d108ef4cdba'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # 1. CREATE TENANT TABLE (skip if exists)
    # =========================================================================
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'tenant' not in existing_tables:
        op.create_table('tenant',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('slug', sa.String(50), nullable=False),
            sa.Column('logo_data', sa.Text()),
            sa.Column('logo_mime_type', sa.String(50)),
            sa.Column('primary_color', sa.String(7), server_default='#0076A8'),
            sa.Column('is_active', sa.Boolean(), server_default='1'),
            sa.Column('is_archived', sa.Boolean(), server_default='0'),
            sa.Column('archived_at', sa.DateTime()),
            sa.Column('archived_by_id', sa.Integer()),
            sa.Column('settings', sa.JSON()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
            sa.Column('created_by_id', sa.Integer()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_tenant_slug', 'tenant', ['slug'], unique=True)
        op.create_index('ix_tenant_is_active', 'tenant', ['is_active'])
        op.create_index('ix_tenant_is_archived', 'tenant', ['is_archived'])
    
    # =========================================================================
    # 2. CREATE TENANT MEMBERSHIP TABLE (skip if exists)
    # =========================================================================
    if 'tenant_membership' not in existing_tables:
        op.create_table('tenant_membership',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tenant_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(20), nullable=False, server_default='member'),
            sa.Column('is_default', sa.Boolean(), server_default='0'),
            sa.Column('joined_at', sa.DateTime()),
            sa.Column('invited_by_id', sa.Integer()),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['invited_by_id'], ['user.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('tenant_id', 'user_id', name='unique_tenant_user')
        )
        op.create_index('ix_tenant_membership_tenant_id', 'tenant_membership', ['tenant_id'])
        op.create_index('ix_tenant_membership_user_id', 'tenant_membership', ['user_id'])
    
    # =========================================================================
    # 3. CREATE TENANT API KEY TABLE (skip if exists)
    # =========================================================================
    if 'tenant_api_key' not in existing_tables:
        op.create_table('tenant_api_key',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tenant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('key_hash', sa.String(128), nullable=False),
            sa.Column('key_prefix', sa.String(8), nullable=False),
            sa.Column('scopes', sa.JSON()),
            sa.Column('is_active', sa.Boolean(), server_default='1'),
            sa.Column('expires_at', sa.DateTime()),
            sa.Column('last_used_at', sa.DateTime()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('created_by_id', sa.Integer()),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by_id'], ['user.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_tenant_api_key_tenant_id', 'tenant_api_key', ['tenant_id'])
    
    # =========================================================================
    # 4. EXTEND USER TABLE (check if columns exist)
    # =========================================================================
    user_columns = [col['name'] for col in inspector.get_columns('user')]
    
    with op.batch_alter_table('user') as batch_op:
        if 'is_superadmin' not in user_columns:
            batch_op.add_column(sa.Column('is_superadmin', sa.Boolean(), server_default='0'))
            batch_op.create_index('ix_user_is_superadmin', ['is_superadmin'])
        if 'current_tenant_id' not in user_columns:
            batch_op.add_column(sa.Column('current_tenant_id', sa.Integer()))
            batch_op.create_index('ix_user_current_tenant_id', ['current_tenant_id'])
            batch_op.create_foreign_key('fk_user_current_tenant', 'tenant', ['current_tenant_id'], ['id'])
    
    # =========================================================================
    # 5. ADD tenant_id TO ALL TENANT-AWARE TABLES
    # =========================================================================
    
    def add_tenant_id_to_table(table_name):
        """Helper to add tenant_id if not exists"""
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if 'tenant_id' not in columns:
            with op.batch_alter_table(table_name) as batch_op:
                batch_op.add_column(sa.Column('tenant_id', sa.Integer()))
                batch_op.create_index(f'ix_{table_name}_tenant_id', ['tenant_id'])
                batch_op.create_foreign_key(f'fk_{table_name}_tenant', 'tenant', ['tenant_id'], ['id'])
    
    # Core tables
    for table_name in ['team', 'entity', 'tax_type', 'task_preset', 'task', 'notification', 'audit_log']:
        if table_name in existing_tables:
            add_tenant_id_to_table(table_name)
    
    # Projects module tables
    for table_name in ['project', 'issue', 'sprint']:
        if table_name in existing_tables:
            add_tenant_id_to_table(table_name)
    
    # =========================================================================
    # 6. UPDATE UNIQUE CONSTRAINTS (per-tenant uniqueness)
    # =========================================================================
    
    # Note: SQLite doesn't support dropping constraints easily
    # These will be handled by application logic for now
    
    # =========================================================================
    # 7. ADD TENANT FOREIGN KEYS TO TENANT TABLE
    # =========================================================================
    # Foreign keys for tenant table are already defined in create_table


def downgrade():
    # Remove foreign keys from tenant table
    with op.batch_alter_table('tenant') as batch_op:
        batch_op.drop_constraint('fk_tenant_archived_by', type_='foreignkey')
        batch_op.drop_constraint('fk_tenant_created_by', type_='foreignkey')
    
    # Remove tenant_id from project tables
    project_tables = ['sprint', 'issue', 'project']
    for table_name in project_tables:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(f'fk_{table_name}_tenant', type_='foreignkey')
            batch_op.drop_index(f'ix_{table_name}_tenant_id')
            batch_op.drop_column('tenant_id')
    
    # Remove tenant_id from core tables
    core_tables = ['audit_log', 'notification', 'task', 'task_preset', 'tax_type', 'entity', 'team']
    for table_name in core_tables:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(f'fk_{table_name}_tenant', type_='foreignkey')
            batch_op.drop_index(f'ix_{table_name}_tenant_id')
            batch_op.drop_column('tenant_id')
    
    # Remove user extensions
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_constraint('fk_user_current_tenant', type_='foreignkey')
        batch_op.drop_index('ix_user_current_tenant_id')
        batch_op.drop_index('ix_user_is_superadmin')
        batch_op.drop_column('current_tenant_id')
        batch_op.drop_column('is_superadmin')
    
    # Drop tables
    op.drop_table('tenant_api_key')
    op.drop_table('tenant_membership')
    op.drop_index('ix_tenant_is_archived', 'tenant')
    op.drop_index('ix_tenant_is_active', 'tenant')
    op.drop_index('ix_tenant_slug', 'tenant')
    op.drop_table('tenant')
