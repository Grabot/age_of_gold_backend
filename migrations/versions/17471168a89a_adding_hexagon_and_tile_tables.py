"""adding hexagon and tile tables

Revision ID: 17471168a89a
Revises: 46bb807f5616
Create Date: 2022-05-29 17:10:07.175984

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17471168a89a'
down_revision = '46bb807f5616'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Hexagon',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=True),
    sa.Column('r', sa.Integer(), nullable=True),
    sa.Column('s', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('Tile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Tile')
    op.drop_table('Hexagon')
    # ### end Alembic commands ###
