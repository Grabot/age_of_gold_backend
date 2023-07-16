"""update guild object

Revision ID: 2e2b6e6c067a
Revises: 236b3e0889c4
Create Date: 2023-07-12 20:15:57.086801

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2e2b6e6c067a"
down_revision = "236b3e0889c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("Guild", sa.Column("default_crest", sa.Boolean(), nullable=False))
    op.drop_column("Guild", "guild_crest")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "Guild", sa.Column("guild_crest", sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.drop_column("Guild", "default_crest")
    # ### end Alembic commands ###