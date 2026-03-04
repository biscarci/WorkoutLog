"""add workout display order

Revision ID: b1f3c9a8d201
Revises: 9efe0606dd27
Create Date: 2026-03-04 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1f3c9a8d201'
down_revision = '9efe0606dd27'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('workout', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('workout', schema=None) as batch_op:
        batch_op.drop_column('display_order')
