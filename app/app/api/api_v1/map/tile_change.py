import json
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Hexagon, Tile, User
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token, get_hex_room


class TileChangeRequest(BaseModel):
    q: int
    r: int
    type: int


@api_router_v1.post("/tile/change", status_code=200)
async def tile_change(
    tile_change_request: TileChangeRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("An error occurred", response)

    tile_q = tile_change_request.q
    tile_r = tile_change_request.r
    tile_type = tile_change_request.type

    tile_statement = select(Tile).filter_by(q=tile_q, r=tile_r).options(selectinload(Tile.hexagon))
    results_tile = await db.execute(tile_statement)
    result_tile = results_tile.first()
    if result_tile is None:
        return get_failed_response("User not found", response)
    tile: Tile = result_tile.Tile

    tile_hexagon: Hexagon = tile.hexagon

    user.lock_tile_setting(1)
    tile.update_tile_info(tile_type, user.id)
    db.add(tile)
    db.add(user)
    room = get_hex_room(tile_hexagon.q, tile_hexagon.r)
    # Emit the results to the hex room.
    await sio.emit(
        "change_tile_type_success",
        tile.serialize_full,
        room=room,
    )

    # We can get all the tiles and re-write the tiles_detail
    # But we will just look for the correct tile in the existing string
    # and update just that one.
    prev_details = json.loads(tile_hexagon.tiles_detail)
    for tile_detail in prev_details:
        if tile_detail["q"] == tile.q and tile_detail["r"] == tile.r:
            tile_detail["type"] = tile.type
    tile_hexagon.tiles_detail = json.dumps(prev_details)
    db.add(tile_hexagon)
    await db.commit()

    return {
        "result": True,
        "tile_lock": user.get_tile_lock().strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }
