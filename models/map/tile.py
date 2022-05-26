from db import db, metadata, sqlalchemy

tiles = sqlalchemy.Table(
    "tiles",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("type", sqlalchemy.Integer),
)


class Tile:
    @classmethod
    async def get(cls, id):
        query = tiles.select().where(tiles.c.id == id)
        tile = await db.fetch_one(query)
        return tile

    @classmethod
    async def create(cls, **tile):
        # probably won't use this
        query = tiles.insert().values(**tile)
        tile_id = await db.execute(query)
        return tile_id

