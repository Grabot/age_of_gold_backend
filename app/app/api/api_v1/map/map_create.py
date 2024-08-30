import os
import stat
import json
import time

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.api_v1.map.map_utils import get_tiles, go_left, go_right, go_left_up, go_right_down, \
    generate_fractal_noise_2d
from app.config.config import settings
from app.database import get_db
from app.models import Hexagon
import numpy as np


@api_router_v1.post("/map/create", status_code=200)
async def create_map(db: AsyncSession = Depends(get_db)) -> dict:
    # This is an initialization function that has to be called after the first deployment.
    start_time = time.time()

    hexagon_select = select(Hexagon).where(Hexagon.q == 0).where(Hexagon.r == 0)
    results = await db.execute(hexagon_select)
    hexagon = results.first()
    if not hexagon:
        np.random.seed(0)
        noise = generate_fractal_noise_2d((2048, 2048), (64, 64), 5)
        print(f"create map of size: {settings.map_size}")

        for row in range(-settings.map_size, settings.map_size+1):
            q = 0
            r = 0
            q_tiles = 0
            r_tiles = 0
            # finding row
            q_tiles += -5 * row
            r_tiles += 9 * row
            r += -1 * row
            # Find the left most hexagon and create the row going to the right
            q += -1 * (settings.map_size + 1)
            q_tiles += -9 * (settings.map_size + 1)
            r_tiles += 4 * (settings.map_size + 1)

            [_, _, _, _] = await go_right(db, q, r, q_tiles, r_tiles, settings.map_size * 2 + 1, noise)
        end_time = time.time()
        total_time = end_time - start_time
        print(f"it took: {total_time} seconds")
        return {"results": "true"}
    else:
        return {"result": True, "message": "map already created"}


@api_router_v1.post("/initialize", status_code=200)
async def initialize_folders() -> dict:

    if not os.path.exists(settings.UPLOAD_FOLDER_AVATARS):
        os.makedirs(settings.UPLOAD_FOLDER_AVATARS)
        os.chmod(settings.UPLOAD_FOLDER_AVATARS, stat.S_IRWXO)
    if not os.path.exists(settings.UPLOAD_FOLDER_CRESTS):
        os.makedirs(settings.UPLOAD_FOLDER_CRESTS)
        os.chmod(settings.UPLOAD_FOLDER_CRESTS, stat.S_IRWXO)
    return {"results": "true"}
