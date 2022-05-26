from models import Tile
from schema import SchemaTile
from app import app


@app.get("/tile/{id}", response_model=SchemaTile)
async def get_tile(id: int):
    tile = await Tile.get(id)
    return SchemaTile(**tile).dict()
