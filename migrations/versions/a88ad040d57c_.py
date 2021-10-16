"""empty message

Revision ID: a88ad040d57c
Revises: 97c188888fad
Create Date: 2021-10-16 16:13:39.586019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a88ad040d57c'
down_revision = '97c188888fad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('venues', 'genres',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('venues', 'genres',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    # ### end Alembic commands ###
