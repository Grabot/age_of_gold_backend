"""added a last changed indicator to tile

Revision ID: a6f5e88d0681
Revises: e1cc800f23f8
Create Date: 2023-01-07 10:12:29.936202

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6f5e88d0681'
down_revision = 'e1cc800f23f8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Tile', sa.Column('last_changed_by', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'Tile', 'User', ['last_changed_by'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'Tile', type_='foreignkey')
    op.drop_column('Tile', 'last_changed_by')
    # ### end Alembic commands ###