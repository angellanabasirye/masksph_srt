"""Clean migration using faculty

Revision ID: cae0e469366b
Revises: 
Create Date: 2025-05-24 16:02:30.386070

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cae0e469366b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('milestones',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('student_milestones',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('milestone_id', sa.Integer(), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('subtasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('milestone_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('sequence_order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('student_subtasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('subtask_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('date_completed', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
    sa.ForeignKeyConstraint(['subtask_id'], ['subtasks.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('student_milestone')
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.drop_constraint('student_supervisor_id_fkey', type_='foreignkey')
        batch_op.drop_column('supervisor_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('supervisor_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('student_supervisor_id_fkey', 'supervisor', ['supervisor_id'], ['id'])

    op.create_table('supervisor',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('supervisor_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('full_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('department', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('phone', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('gender', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    sa.Column('professional_field', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='supervisor_pkey'),
    sa.UniqueConstraint('email', name='supervisor_email_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('student_milestone',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('student_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('milestone_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('completed', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestone.id'], name='student_milestone_milestone_id_fkey'),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], name='student_milestone_student_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='student_milestone_pkey')
    )
    op.create_table('milestone',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='milestone_pkey')
    )
    op.drop_table('student_subtasks')
    op.drop_table('subtasks')
    op.drop_table('student_milestones')
    op.drop_table('milestones')
    # ### end Alembic commands ###
