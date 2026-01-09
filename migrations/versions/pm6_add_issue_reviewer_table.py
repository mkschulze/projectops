"""Add IssueReviewer table for multi-stage approval workflow

Revision ID: pm6_issue_reviewer
Revises: pm6_issue_details
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pm6_issue_reviewer'
down_revision = 'pm6_issue_details'
branch_labels = None
depends_on = None


def upgrade():
    # Create issue_reviewer table for multi-stage approval workflow
    op.create_table('issue_reviewer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), default=1),
        sa.Column('has_approved', sa.Boolean(), default=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approval_note', sa.Text(), nullable=True),
        sa.Column('has_rejected', sa.Boolean(), default=False),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['issue_id'], ['issue.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('issue_id', 'user_id', name='unique_issue_reviewer')
    )
    op.create_index('ix_issue_reviewer_issue_id', 'issue_reviewer', ['issue_id'])
    op.create_index('ix_issue_reviewer_user_id', 'issue_reviewer', ['user_id'])


def downgrade():
    op.drop_index('ix_issue_reviewer_user_id', table_name='issue_reviewer')
    op.drop_index('ix_issue_reviewer_issue_id', table_name='issue_reviewer')
    op.drop_table('issue_reviewer')
