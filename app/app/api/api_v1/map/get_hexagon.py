from typing import List

from config import settings
from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy import tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from util.util import get_wraparounds

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import Hexagon


class HexagonRequest(BaseModel):
    q: int
    r: int


class HexagonListRequest(BaseModel):
    hexagons: List[HexagonRequest]


@api_router_v1.post("/hexagon/get", status_code=200)
async def get_hexagon(
    hexagon_list_request: HexagonListRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> dict:
    map_size = settings.map_size
    is_wrapped = False
    hex_retrieve = []
    hex_retrieve_wrapped = []
    for hexagon in hexagon_list_request.hexagons:
        hex_q = hexagon.q
        hex_r = hexagon.r
        # If the hex is out of the map bounds we want it to loop around
        if hex_q < -map_size or hex_q > map_size or hex_r < -map_size or hex_r > map_size:
            [hex_q, wrap_q, hex_r, wrap_r] = get_wraparounds(hex_q, hex_r)

            hex_retrieve_wrapped.append([hex_q, hex_r, wrap_q, wrap_r])
            is_wrapped = True
        hex_retrieve.append([hex_q, hex_r])
    print(f"hex_retrieve {hex_retrieve}")
    hexes_return = []
    if hex_retrieve:
        statement_hexes = select(Hexagon).filter(tuple_(Hexagon.q, Hexagon.r).in_(hex_retrieve))
        results = await db.execute(statement_hexes)
        hexes = results.all()
        for hex in hexes:
            hexagon = hex.Hexagon
            return_hexagon = hexagon.serialize
            if is_wrapped:
                for hex_wrapped in hex_retrieve_wrapped:
                    if hexagon.q == hex_wrapped[0] and hexagon.r == hex_wrapped[1]:
                        return_hexagon["wraparound"] = {
                            "q": hex_wrapped[2],
                            "r": hex_wrapped[3],
                        }
                        break
            hexes_return.append(return_hexagon)

    return {
        "result": True,
        "hexagons": hexes_return,
    }
