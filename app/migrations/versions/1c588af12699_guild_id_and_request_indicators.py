"""guild id and request indicators

Revision ID: 1c588af12699
Revises: 2e2b6e6c067a
Create Date: 2023-07-16 14:39:07.158565

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1c588af12699"
down_revision = "2e2b6e6c067a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("Guild", sa.Column("guild_id", sa.Integer(), nullable=False))
    op.add_column("Guild", sa.Column("accepted", sa.Boolean(), nullable=False))
    op.add_column("Guild", sa.Column("requested", sa.Boolean(), nullable=True))
    op.create_index(op.f("ix_Guild_guild_id"), "Guild", ["guild_id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_Guild_guild_id"), table_name="Guild")
    op.drop_column("Guild", "requested")
    op.drop_column("Guild", "accepted")
    op.drop_column("Guild", "guild_id")
    # ### end Alembic commands ###
