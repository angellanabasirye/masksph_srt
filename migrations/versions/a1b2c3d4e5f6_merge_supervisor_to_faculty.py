"""Migrate student_supervisors to use faculty_id instead of supervisor_id"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = ('168e3dda033b') 
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old table if it exists
    # op.drop_table('student_supervisors')
    from sqlalchemy import text

    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS student_supervisors CASCADE"))


    # Recreate with updated foreign keys pointing to faculty
    op.create_table(
        'student_supervisors',
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('student.id'), primary_key=True),
        sa.Column('faculty_id', sa.Integer(), sa.ForeignKey('faculty.id'), primary_key=True)
    )


def downgrade():
    # Drop the new version
    op.drop_table('student_supervisors')

    # Recreate old version referencing Supervisor (optional)
    op.create_table(
        'student_supervisors',
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('student.id'), primary_key=True),
        sa.Column('supervisor_id', sa.Integer(), sa.ForeignKey('supervisor.id'), primary_key=True)
    )
