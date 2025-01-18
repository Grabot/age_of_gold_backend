"""adding all tables

Revision ID: a20fdbbdb51e
Revises: 
Create Date: 2025-01-17 18:55:56.368380

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'a20fdbbdb51e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Hexagon',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('tiles_detail', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Hexagon'))
    )
    op.create_index('hexagon_index', 'Hexagon', ['q', 'r'], unique=True)
    op.create_table('User',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('salt', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('about_me', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('origin', sa.Integer(), nullable=False),
    sa.Column('tile_lock', sa.DateTime(), nullable=False),
    sa.Column('email_verified', sa.Boolean(), nullable=False),
    sa.Column('default_avatar', sa.Boolean(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_User'))
    )
    op.create_index(op.f('ix_User_username'), 'User', ['username'], unique=True)
    op.create_index('user_index', 'User', ['email_hash', 'origin'], unique=True)
    op.create_table('Friend',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('friend_id', sa.Integer(), nullable=False),
    sa.Column('friend_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('unread_messages', sa.Integer(), nullable=False),
    sa.Column('accepted', sa.Boolean(), nullable=False),
    sa.Column('ignored', sa.Boolean(), nullable=False),
    sa.Column('requested', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['friend_id'], ['User.id'], name=op.f('fk_Friend_friend_id_User')),
    sa.ForeignKeyConstraint(['user_id'], ['User.id'], name=op.f('fk_Friend_user_id_User')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Friend'))
    )
    op.create_table('GlobalMessage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('sender_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['sender_id'], ['User.id'], name=op.f('fk_GlobalMessage_sender_id_User')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_GlobalMessage'))
    )
    op.create_index(op.f('ix_GlobalMessage_timestamp'), 'GlobalMessage', ['timestamp'], unique=False)
    op.create_table('Guild',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guild_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('guild_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('default_crest', sa.Boolean(), nullable=False),
    sa.Column('member_ids', sa.ARRAY(sa.Integer()), nullable=True),
    sa.Column('unread_messages', sa.Integer(), nullable=False),
    sa.Column('accepted', sa.Boolean(), nullable=False),
    sa.Column('requested', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['User.id'], name=op.f('fk_Guild_user_id_User')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Guild'))
    )
    op.create_index(op.f('ix_Guild_guild_id'), 'Guild', ['guild_id'], unique=False)
    op.create_table('GuildMessage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('guild_id', sa.Integer(), nullable=False),
    sa.Column('sender_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['sender_id'], ['User.id'], name=op.f('fk_GuildMessage_sender_id_User')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_GuildMessage'))
    )
    op.create_index(op.f('ix_GuildMessage_guild_id'), 'GuildMessage', ['guild_id'], unique=False)
    op.create_index(op.f('ix_GuildMessage_timestamp'), 'GuildMessage', ['timestamp'], unique=False)
    op.create_table('PersonalMessage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('receiver_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['receiver_id'], ['User.id'], name=op.f('fk_PersonalMessage_receiver_id_User')),
    sa.ForeignKeyConstraint(['user_id'], ['User.id'], name=op.f('fk_PersonalMessage_user_id_User')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_PersonalMessage'))
    )
    op.create_index(op.f('ix_PersonalMessage_timestamp'), 'PersonalMessage', ['timestamp'], unique=False)
    op.create_table('Tile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hexagon_id', sa.Integer(), nullable=False),
    sa.Column('q', sa.Integer(), nullable=False),
    sa.Column('r', sa.Integer(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('last_changed_by', sa.Integer(), nullable=True),
    sa.Column('last_changed_time', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['hexagon_id'], ['Hexagon.id'], name=op.f('fk_Tile_hexagon_id_Hexagon')),
    sa.ForeignKeyConstraint(['last_changed_by'], ['User.id'], name=op.f('fk_Tile_last_changed_by_User')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Tile'))
    )
    op.create_index('tile_id_index', 'Tile', ['id'], unique=True)
    op.create_index('tile_q_r_index', 'Tile', ['q', 'r'], unique=True)
    op.create_table('UserToken',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('access_token', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('token_expiration', sa.Integer(), nullable=False),
    sa.Column('refresh_token', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('refresh_token_expiration', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['User.id'], name=op.f('fk_UserToken_user_id_User')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_UserToken'))
    )
    op.create_index(op.f('ix_UserToken_access_token'), 'UserToken', ['access_token'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_UserToken_access_token'), table_name='UserToken')
    op.drop_table('UserToken')
    op.drop_index('tile_q_r_index', table_name='Tile')
    op.drop_index('tile_id_index', table_name='Tile')
    op.drop_table('Tile')
    op.drop_index(op.f('ix_PersonalMessage_timestamp'), table_name='PersonalMessage')
    op.drop_table('PersonalMessage')
    op.drop_index(op.f('ix_GuildMessage_timestamp'), table_name='GuildMessage')
    op.drop_index(op.f('ix_GuildMessage_guild_id'), table_name='GuildMessage')
    op.drop_table('GuildMessage')
    op.drop_index(op.f('ix_Guild_guild_id'), table_name='Guild')
    op.drop_table('Guild')
    op.drop_index(op.f('ix_GlobalMessage_timestamp'), table_name='GlobalMessage')
    op.drop_table('GlobalMessage')
    op.drop_table('Friend')
    op.drop_index('user_index', table_name='User')
    op.drop_index(op.f('ix_User_username'), table_name='User')
    op.drop_table('User')
    op.drop_index('hexagon_index', table_name='Hexagon')
    op.drop_table('Hexagon')
    # ### end Alembic commands ###