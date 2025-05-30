"""Add user_id to student

Revision ID: 4c2b7144148a
Revises: ce4fed68a25d
Create Date: 2025-05-25 17:27:05.372618

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c2b7144148a'
down_revision = 'ce4fed68a25d'
branch_labels = None
depends_on = None


# def upgrade():
#     # ### commands auto generated by Alembic - please adjust! ###
#     with op.batch_alter_table('student', schema=None) as batch_op:
#         batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=False))
#         batch_op.create_unique_constraint(None, ['user_id'])
#         batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])
#         batch_op.drop_column('phone')

#     # ### end Alembic commands ###

def upgrade():
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint(None, ['user_id'])
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###
