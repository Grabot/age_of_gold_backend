"""removing removed indicator on friend object

Revision ID: 92d4ae706d06
Revises: 24682eecd8d3
Create Date: 2023-05-12 13:42:43.256266

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "92d4ae706d06"
down_revision = "24682eecd8d3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Friend", schema=None) as batch_op:
        batch_op.drop_column("removed")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Friend", schema=None) as batch_op:
        batch_op.add_column(sa.Column("removed", sa.BOOLEAN(), autoincrement=False, nullable=True))

    # ### end Alembic commands ###