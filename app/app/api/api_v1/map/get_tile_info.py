from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Tile, User
from app.util.util import check_token, get_auth_token


class GetTileInfoRequest(BaseModel):
    q: int
    r: int


@api_router_v1.post("/tile/get/info", status_code=200)
async def get_tile_info(
    get_tile_info_request: GetTileInfoRequest,
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

    tile_q = get_tile_info_request.q
    tile_r = get_tile_info_request.r

    tile_statement = (
        select(Tile).filter_by(q=tile_q, r=tile_r).options(selectinload(Tile.user_changed))
    )
    results_tile = await db.execute(tile_statement)
    result_tile = results_tile.first()
    if result_tile is None:
        return get_failed_response("User not found", response)
    tile = result_tile.Tile

    return {"result": True, "tile": tile.serialize_full}
