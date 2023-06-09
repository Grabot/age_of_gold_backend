"""initial commit User and Friend

Revision ID: d59cee3a9f40
Revises:
Create Date: 2023-06-02 19:22:59.087494

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "d59cee3a9f40"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "User",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("about_me", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.Column("origin", sa.Integer(), nullable=False),
        sa.Column("token", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("token_expiration", sa.Integer(), nullable=True),
        sa.Column("tile_lock", sa.DateTime(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("default_avatar", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_User")),
    )
    op.create_index(op.f("ix_User_token"), "User", ["token"], unique=False)
    op.create_index(op.f("ix_User_username"), "User", ["username"], unique=True)
    op.create_index("user_index", "User", ["email", "origin"], unique=True)
    op.create_table(
        "Friend",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("friend_id", sa.Integer(), nullable=True),
        sa.Column("last_time_activity", sa.DateTime(), nullable=False),
        sa.Column("unread_messages", sa.Integer(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("ignored", sa.Boolean(), nullable=False),
        sa.Column("requested", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["friend_id"], ["User.id"], name=op.f("fk_Friend_friend_id_User")),
        sa.ForeignKeyConstraint(["user_id"], ["User.id"], name=op.f("fk_Friend_user_id_User")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_Friend")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("Friend")
    op.drop_index("user_index", table_name="User")
    op.drop_index(op.f("ix_User_username"), table_name="User")
    op.drop_index(op.f("ix_User_token"), table_name="User")
    op.drop_table("User")
    # ### end Alembic commands ###