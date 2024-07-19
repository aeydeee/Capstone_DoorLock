"""revise the student_id to student_number

Revision ID: 9e90114fc86b
Revises: 11de894d7b70
Create Date: 2024-07-17 01:15:14.351947

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9e90114fc86b'
down_revision = '11de894d7b70'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('student_number', sa.String(length=100), nullable=False))
        batch_op.drop_index('student_id')
        batch_op.create_unique_constraint(None, ['student_number'])
        batch_op.drop_column('student_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('student_id', mysql.VARCHAR(length=100), nullable=False))
        batch_op.drop_constraint(None, type_='unique')
        batch_op.create_index('student_id', ['student_id'], unique=True)
        batch_op.drop_column('student_number')

    # ### end Alembic commands ###