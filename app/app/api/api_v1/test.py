from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import Friend, Hexagon


@api_router_v1.get("/test", status_code=200)
async def get_test(db: AsyncSession = Depends(get_db)) -> dict:
    print("1")
    statement = (
        select(Hexagon)
        .where(Hexagon.q == 0 and Hexagon.r == 0)
        .options(selectinload(Hexagon.tiles))
    )
    results = await db.execute(statement)
    hexagon = results.first()
    print(f"hexagon: {hexagon}")
    print(f"hexagon: {hexagon.Hexagon}")
    print(f"hexagon: {hexagon.Hexagon.tiles}")
    return {"results": "true"}


@api_router_v1.get("/test2", status_code=200)
async def get_test2(db: AsyncSession = Depends(get_db)) -> dict:
    print("1")
    statement = (
        select(Friend)
        .where(Friend.user_id == 1)
        .options(selectinload(Friend.friend))
        .options(selectinload(Friend.follower))
    )
    results = await db.execute(statement)
    friend = results.first()
    print(f"friend: {friend}")
    print(f"friend: {friend.Friend}")
    # print(f"hexagon: {hexagon.Hexagon.tiles}")
    return {"results": friend.Friend.serialize}
