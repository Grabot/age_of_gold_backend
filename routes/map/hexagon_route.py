from models import Hexagon
from schema import SchemaHexagon
from app import app


@app.get("/hexagon/{id}", response_model=SchemaHexagon)
async def get_hexagon(id: int):
    hexagon = await Hexagon.get(id)
    return SchemaHexagon(**hexagon).dict()
