from models import Hexagon
from schema import SchemaHexagon
from app import app


@app.post("/hexagon/")
async def create_hexagon(hexagon: SchemaHexagon):
    hexagon_id = await Hexagon.create(**hexagon.dict())
    return {"hexagon_id": hexagon_id}


@app.get("/hexagon/{id}", response_model=SchemaHexagon)
async def get_hexagon(id: int):
    hexagon = await Hexagon.get(id)
    return SchemaHexagon(**hexagon).dict()
