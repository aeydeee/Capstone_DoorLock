"""fix m_initial attrib in user model

Revision ID: 6a2265708eee
Revises: 8399fa9aa10c
Create Date: 2024-07-17 01:00:34.929932

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '6a2265708eee'
down_revision = '8399fa9aa10c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('m_initial', sa.String(length=5), nullable=False))
        batch_op.drop_column('m_initial_')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('m_initial_', mysql.VARCHAR(length=5), nullable=False))
        batch_op.drop_column('m_initial')

    # ### end Alembic commands ###