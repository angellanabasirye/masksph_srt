"""Add first_login flag to User

Revision ID: ce4fed68a25d
Revises: cae0e469366b
Create Date: 2025-05-25 13:32:53.395487

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce4fed68a25d'
down_revision = 'cae0e469366b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('milestone')
    op.drop_table('supervisor')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_login', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('first_login')

    op.create_table('supervisor',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('full_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('department', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('phone', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('gender', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    sa.Column('professional_field', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='supervisor_pkey'),
    sa.UniqueConstraint('email', name='supervisor_email_key')
    )
    op.create_table('milestone',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='milestone_pkey')
    )
    # ### end Alembic commands ###
