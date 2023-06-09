"""adding sender id to global messages

Revision ID: 116bf92d392e
Revises: 92d4ae706d06
Create Date: 2023-05-29 12:45:58.157396

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "116bf92d392e"
down_revision = "92d4ae706d06"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("GlobalMessage", schema=None) as batch_op:
        batch_op.add_column(sa.Column("sender_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, "User", ["sender_id"], ["id"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("GlobalMessage", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_column("sender_id")

    # ### end Alembic commands ###