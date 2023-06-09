"""adding email to user

Revision ID: 2cd6a6ea940f
Revises: 327317a6b2af
Create Date: 2022-10-05 18:59:26.747750

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2cd6a6ea940f"
down_revision = "327317a6b2af"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("tile_index", table_name="Tile")
    op.create_index("tile_id_index", "Tile", ["id"], unique=True)
    op.create_index("tile_q_r_index", "Tile", ["q", "r"], unique=True)
    op.add_column("User", sa.Column("email", sa.Text(), nullable=True))
    op.create_index(op.f("ix_User_email"), "User", ["email"], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_User_email"), table_name="User")
    op.drop_column("User", "email")
    op.drop_index("tile_q_r_index", table_name="Tile")
    op.drop_index("tile_id_index", table_name="Tile")
    op.create_index("tile_index", "Tile", ["q", "r"], unique=False)
    # ### end Alembic commands ###