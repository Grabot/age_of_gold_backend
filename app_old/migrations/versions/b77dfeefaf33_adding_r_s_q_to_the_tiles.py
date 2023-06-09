"""adding r, s, q to the tiles

Revision ID: b77dfeefaf33
Revises: aeef7488a61c
Create Date: 2022-05-31 17:55:52.986016

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b77dfeefaf33"
down_revision = "aeef7488a61c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("Tile", sa.Column("q", sa.Integer(), nullable=True))
    op.add_column("Tile", sa.Column("r", sa.Integer(), nullable=True))
    op.add_column("Tile", sa.Column("s", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("Tile", "s")
    op.drop_column("Tile", "r")
    op.drop_column("Tile", "q")
    # ### end Alembic commands ###