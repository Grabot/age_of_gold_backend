from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import Hexagon


@api_router_v1.get("/test", status_code=200)
async def get_test(db: AsyncSession = Depends(get_db)) -> dict:
    statement = (
        select(Hexagon)
        .where(Hexagon.q == 0 and Hexagon.r == 0)
        .options(selectinload(Hexagon.tiles))
    )
    results = await db.execute(statement)
    hexagon = results.first()
    return {"results": "true"}
