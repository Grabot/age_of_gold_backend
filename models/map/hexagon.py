from db import db, metadata, sqlalchemy

hexagons = sqlalchemy.Table(
    "hexagons",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("q", sqlalchemy.Integer),
    sqlalchemy.Column("r", sqlalchemy.Integer),
    sqlalchemy.Column("s", sqlalchemy.Integer),
)


class Hexagon:
    @classmethod
    async def get(cls, id):
        query = hexagons.select().where(hexagons.c.id == id)
        hexagon = await db.fetch_one(query)
        return hexagon

    @classmethod
    async def create(cls, **user):
        # probably won't use this
        query = hexagons.insert().values(**user)
        hexagon_id = await db.execute(query)
        return hexagon_id

