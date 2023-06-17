import json
import time

from config.config import settings
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import Hexagon

from .map_utils import get_tiles, go_left, go_left_up, go_right, go_right_down


@api_router_v1.post("/map/create", status_code=200)
async def create_map(db: AsyncSession = Depends(get_db)) -> dict:
    start_time = time.time()
    print("create map!")
    hexagon_select = select(Hexagon).where(Hexagon.q == 0).where(Hexagon.r == 0)
    results = await db.execute(hexagon_select)
    hexagon = results.first()
    if not hexagon:
        q = 0
        r = 0
        q_tiles = 0
        r_tiles = 0
        # center tile with left and right hexagons
        hexagon = Hexagon(q=q, r=r, tiles_detail="{}")
        db.add(hexagon)
        await db.commit()
        await db.refresh(hexagon)
        tiles = get_tiles(hexagon.id, q_tiles, r_tiles)
        tiles_info = []
        for tile in tiles:
            db.add(tile)
            tiles_info.append(tile.serialize)
        hexagon.tiles_detail = json.dumps(tiles_info)
        db.add(hexagon)
        await db.commit()
        [_, _, _, _] = await go_left(db, q, r, q_tiles, r_tiles)
        [_, _, _, _] = await go_right(db, q, r, q_tiles, r_tiles)

        # going up
        for x in range(0, settings.map_size):
            [q, r, q_tiles, r_tiles] = await go_left_up(db, q, r, q_tiles, r_tiles)
            [_, _, _, _] = await go_left(db, q, r, q_tiles, r_tiles)
            [_, _, _, _] = await go_right(db, q, r, q_tiles, r_tiles)

        # going down, we reset back to the center for this.
        q = 0
        r = 0
        q_tiles = 0
        r_tiles = 0
        for x in range(0, settings.map_size):
            [q, r, q_tiles, r_tiles] = await go_right_down(db, q, r, q_tiles, r_tiles)
            [_, _, _, _] = await go_left(db, q, r, q_tiles, r_tiles)
            [_, _, _, _] = await go_right(db, q, r, q_tiles, r_tiles)
        end_time = time.time()
        total_time = end_time - start_time
        print(f"it took: {total_time} seconds")
        return {"results": "true"}
    else:
        return {"result": True, "message": "map already created"}
