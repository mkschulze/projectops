"""PM-6: Add Issue Details tables (comments, attachments, links, worklogs)

Revision ID: pm6_issue_details
Revises: pm2_issue_system
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'pm6_issue_details'
down_revision = 'pm2_issue_system'
branch_labels = None
depends_on = None


def upgrade():
    # Issue Comments table
    op.create_table('issue_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['issue_id'], ['issue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issue_comment_issue_id'), 'issue_comment', ['issue_id'], unique=False)

    # Issue Attachments table
    op.create_table('issue_attachment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('filepath', sa.String(length=500), nullable=False),
        sa.Column('filesize', sa.Integer(), nullable=True),
        sa.Column('mimetype', sa.String(length=100), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['issue_id'], ['issue.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issue_attachment_issue_id'), 'issue_attachment', ['issue_id'], unique=False)

    # Issue Links table
    op.create_table('issue_link',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_issue_id', sa.Integer(), nullable=False),
        sa.Column('target_issue_id', sa.Integer(), nullable=False),
        sa.Column('link_type', sa.String(length=50), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['source_issue_id'], ['issue.id'], ),
        sa.ForeignKeyConstraint(['target_issue_id'], ['issue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issue_link_source_issue_id'), 'issue_link', ['source_issue_id'], unique=False)
    op.create_index(op.f('ix_issue_link_target_issue_id'), 'issue_link', ['target_issue_id'], unique=False)

    # Worklog table
    op.create_table('worklog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('time_spent', sa.Integer(), nullable=False),
        sa.Column('work_date', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['issue_id'], ['issue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_worklog_issue_id'), 'worklog', ['issue_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_worklog_issue_id'), table_name='worklog')
    op.drop_table('worklog')
    
    op.drop_index(op.f('ix_issue_link_target_issue_id'), table_name='issue_link')
    op.drop_index(op.f('ix_issue_link_source_issue_id'), table_name='issue_link')
    op.drop_table('issue_link')
    
    op.drop_index(op.f('ix_issue_attachment_issue_id'), table_name='issue_attachment')
    op.drop_table('issue_attachment')
    
    op.drop_index(op.f('ix_issue_comment_issue_id'), table_name='issue_comment')
    op.drop_table('issue_comment')
