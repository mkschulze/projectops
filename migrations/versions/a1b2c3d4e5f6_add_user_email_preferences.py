"""Add user email preferences

Revision ID: a1b2c3d4e5f6
Revises: fd1a6046118a
Create Date: 2025-12-30 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'fd1a6046118a'
branch_labels = None
depends_on = None


def upgrade():
    # Add email notification preference columns to user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_notifications', sa.Boolean(), nullable=True, default=True))
        batch_op.add_column(sa.Column('email_on_assignment', sa.Boolean(), nullable=True, default=True))
        batch_op.add_column(sa.Column('email_on_status_change', sa.Boolean(), nullable=True, default=True))
        batch_op.add_column(sa.Column('email_on_due_reminder', sa.Boolean(), nullable=True, default=True))
        batch_op.add_column(sa.Column('email_on_comment', sa.Boolean(), nullable=True, default=False))
    
    # Set defaults for existing users
    op.execute("UPDATE user SET email_notifications = 1 WHERE email_notifications IS NULL")
    op.execute("UPDATE user SET email_on_assignment = 1 WHERE email_on_assignment IS NULL")
    op.execute("UPDATE user SET email_on_status_change = 1 WHERE email_on_status_change IS NULL")
    op.execute("UPDATE user SET email_on_due_reminder = 1 WHERE email_on_due_reminder IS NULL")
    op.execute("UPDATE user SET email_on_comment = 0 WHERE email_on_comment IS NULL")


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('email_on_comment')
        batch_op.drop_column('email_on_due_reminder')
        batch_op.drop_column('email_on_status_change')
        batch_op.drop_column('email_on_assignment')
        batch_op.drop_column('email_notifications')
