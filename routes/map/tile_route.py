from models import Tile
from schema import SchemaTile
from app import app


@app.post("/tile/")
async def create_tile(tile: SchemaTile):
    tile_id = await Tile.create(**tile.dict())
    return {"tile_id": tile_id}


@app.get("/tile/{id}", response_model=SchemaTile)
async def get_tile(id: int):
    tile = await Tile.get(id)
    return SchemaTile(**tile).dict()
