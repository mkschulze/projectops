"""Add flexible issue system with configurable types and statuses

Revision ID: pm2_issue_system
Revises: fca1f9beaa9f
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pm2_issue_system'
down_revision = 'fca1f9beaa9f'
branch_labels = None
depends_on = None


def upgrade():
    # Add methodology and terminology to project
    op.add_column('project', sa.Column('methodology', sa.String(20), server_default='scrum'))
    op.add_column('project', sa.Column('terminology', sa.JSON(), nullable=True))
    
    # Create issue_type table
    op.create_table('issue_type',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('name_en', sa.String(50), nullable=True),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('icon', sa.String(50), server_default='bi-card-checklist'),
        sa.Column('color', sa.String(7), server_default='#86BC25'),
        sa.Column('hierarchy_level', sa.Integer(), server_default='1'),
        sa.Column('can_have_children', sa.Boolean(), server_default='1'),
        sa.Column('allowed_child_types', sa.JSON(), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default='0'),
        sa.Column('is_subtask', sa.Boolean(), server_default='0'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='unique_issue_type_per_project')
    )
    
    # Create issue_status table
    op.create_table('issue_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('name_en', sa.String(50), nullable=True),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('category', sa.String(20), server_default='todo'),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('color', sa.String(7), server_default='#75787B'),
        sa.Column('is_initial', sa.Boolean(), server_default='0'),
        sa.Column('is_final', sa.Boolean(), server_default='0'),
        sa.Column('allowed_transitions', sa.JSON(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='unique_status_per_project')
    )
    
    # Create sprint table
    op.create_table('sprint',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('state', sa.String(20), server_default='future'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sprint_project_id', 'sprint', ['project_id'])
    
    # Create issue table
    op.create_table('issue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(20), nullable=False),
        sa.Column('type_id', sa.Integer(), nullable=False),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('summary', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('reporter_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='3'),
        sa.Column('original_estimate', sa.Integer(), nullable=True),
        sa.Column('time_spent', sa.Integer(), server_default='0'),
        sa.Column('remaining_estimate', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('resolution_date', sa.DateTime(), nullable=True),
        sa.Column('sprint_id', sa.Integer(), nullable=True),
        sa.Column('story_points', sa.Float(), nullable=True),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('custom_fields', sa.JSON(), nullable=True),
        sa.Column('board_position', sa.Integer(), server_default='0'),
        sa.Column('backlog_position', sa.Integer(), server_default='0'),
        sa.Column('is_archived', sa.Boolean(), server_default='0'),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['type_id'], ['issue_type.id'], ),
        sa.ForeignKeyConstraint(['status_id'], ['issue_status.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['issue.id'], ),
        sa.ForeignKeyConstraint(['assignee_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['reporter_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['sprint_id'], ['sprint.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_issue_project_id', 'issue', ['project_id'])
    op.create_index('ix_issue_key', 'issue', ['key'], unique=True)
    op.create_index('ix_issue_assignee_id', 'issue', ['assignee_id'])
    op.create_index('ix_issue_parent_id', 'issue', ['parent_id'])
    op.create_index('ix_issue_sprint_id', 'issue', ['sprint_id'])


def downgrade():
    op.drop_table('issue')
    op.drop_table('sprint')
    op.drop_table('issue_status')
    op.drop_table('issue_type')
    op.drop_column('project', 'terminology')
    op.drop_column('project', 'methodology')
