import json
import time

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.api_v1.map.map_utils import go_right, generate_fractal_noise_2d
from app.config.config import settings
from app.database import get_db
from app.models import Hexagon
import numpy as np


class MapCreateRowRequest(BaseModel):
    row: int


@api_router_v1.post("/map/create/row", status_code=200)
async def create_map_row(
        map_create_row_request: MapCreateRowRequest,
        db: AsyncSession = Depends(get_db)
) -> dict:
    # This is an initialization function that has to be called after the first deployment.
    start_time = time.time()

    row = map_create_row_request.row

    print(f"create row {row} of map with size: {settings.map_size}")
    q = 0
    r = 0
    q_tiles = 0
    r_tiles = 0

    # finding row
    q_tiles += -5 * row
    r_tiles += 9 * row
    r += -1 * row

    # Create center hexagon
    hexagon_select = select(Hexagon).where(Hexagon.q == q).where(Hexagon.r == r)
    results = await db.execute(hexagon_select)
    hexagon = results.first()
    if not hexagon:
        np.random.seed(0)
        noise = generate_fractal_noise_2d((8192, 8192), (64, 64), 5)

        # Find the left most hexagon and create the row going to the right
        q += -1 * (settings.map_size + 1)
        q_tiles += -9 * (settings.map_size + 1)
        r_tiles += 4 * (settings.map_size + 1)

        [_, _, _, _] = await go_right(db, q, r, q_tiles, r_tiles, settings.map_size * 2 + 1, noise)

        end_time = time.time()
        total_time = end_time - start_time
        print(f"it took: {total_time} seconds")
        return {"results": f"row {row} created"}
    else:
        return {"results": f"row {row} already exists"}
