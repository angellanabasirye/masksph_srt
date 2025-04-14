"""Add activity log model

Revision ID: 54de298f9b0e
Revises: c61b1e54807f
Create Date: 2025-04-14 13:21:50.913205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54de298f9b0e'
down_revision = 'c61b1e54807f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activity_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=255), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('activity_log')
    # ### end Alembic commands ###
